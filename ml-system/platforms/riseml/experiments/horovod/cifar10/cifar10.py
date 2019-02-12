'''Train a simple deep CNN on the CIFAR10 small images dataset.

Uses Horovod to distribute the training.
'''

from __future__ import print_function
import keras
import os
import pickle
import numpy as np
import argparse
import riseml
import math
import tensorflow as tf
import horovod.keras as hvd

from keras.datasets.cifar import load_batch
from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K

OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/output')


def download_data(num_classes=10):
    (x_train, y_train), (x_test, y_test) = cifar10.load_data()
    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)
    return (x_train, y_train), (x_test, y_test)


def get_data(path, num_classes=10):
    num_train_samples = 50000

    x_train = np.zeros((num_train_samples, 3, 32, 32), dtype='uint8')
    y_train = np.zeros((num_train_samples,), dtype='uint8')

    for i in range(1, 6):
        fpath = os.path.join(path, 'data_batch_' + str(i))
        data, labels = load_batch(fpath)
        x_train[(i - 1) * 10000:i * 10000, :, :, :] = data
        y_train[(i - 1) * 10000:i * 10000] = labels

    fpath = os.path.join(path, 'test_batch')
    x_test, y_test = load_batch(fpath)

    y_train = np.reshape(y_train, (len(y_train), 1))
    y_test = np.reshape(y_test, (len(y_test), 1))

    x_train = x_train.transpose(0, 2, 3, 1)
    x_test = x_test.transpose(0, 2, 3, 1)

    # Convert class vectors to binary class matrices.
    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)

    return (x_train, y_train), (x_test, y_test)


def get_model(input_shape, lr, lr_decay, num_classes=10):
    model = Sequential()

    model.add(Conv2D(64, (3, 3), padding='same',
                    input_shape=input_shape))
    model.add(Activation('relu'))
    model.add(Conv2D(64, (3, 3)))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Conv2D(256, (3, 3), padding='same'))
    model.add(Activation('relu'))
    model.add(Conv2D(256, (3, 3)))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Flatten())
    model.add(Dense(1024))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes))
    model.add(Activation('softmax'))

    # initiate RMSprop optimizer
    opt = keras.optimizers.rmsprop(lr=lr, decay=lr_decay)

    opt = hvd.DistributedOptimizer(opt)

    # Let's train the model using RMSprop
    model.compile(loss='categorical_crossentropy',
                optimizer=opt,
                metrics=['accuracy'])
    return model


def train_model(model, xy_train, xy_test,
                tensorboard_dir,
                data_augmentation=False, epochs=200, batch_size=32):

    x_train, y_train = xy_train
    x_test, y_test = xy_test
    print('x_train shape:', x_train.shape)
    print(x_train.shape[0], 'train samples')
    print(x_test.shape[0], 'test samples')

    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')
    x_train /= 255
    x_test /= 255

    if not data_augmentation:
        print('Not using data augmentation.')
        model.fit(x_train, y_train,
                batch_size=batch_size,
                epochs=epochs,
                validation_data=(x_test, y_test),
                verbose=2,
                shuffle=True)
    else:
        print('Using real-time data augmentation.')
        # This will do preprocessing and realtime data augmentation:
        datagen = ImageDataGenerator(
            featurewise_center=False,  # set input mean to 0 over the dataset
            samplewise_center=False,  # set each sample mean to 0
            featurewise_std_normalization=False,  # divide inputs by std of the dataset
            samplewise_std_normalization=False,  # divide each input by its std
            zca_whitening=False,  # apply ZCA whitening
            rotation_range=0,  # randomly rotate images in the range (degrees, 0 to 180)
            width_shift_range=0.1,  # randomly shift images horizontally (fraction of total width)
            height_shift_range=0.1,  # randomly shift images vertically (fraction of total height)
            horizontal_flip=True,  # randomly flip images
            vertical_flip=False)  # randomly flip images

        # Compute quantities required for feature-wise normalization
        # (std, mean, and principal components if ZCA whitening is applied).
        datagen.fit(x_train)

        callbacks = [
            # Horovod: broadcast initial variable states from rank 0 to all other processes.
            # This is necessary to ensure consistent initialization of all workers when
            # training is started with random weights or restored from a checkpoint.
            hvd.callbacks.BroadcastGlobalVariablesCallback(0),
        ]

        verbose = 0

        # Horovod: save checkpoints only on worker 0 to prevent other workers from corrupting them.
        if hvd.rank() == 0:
            checkpoint = os.path.join(OUTPUT_DIR,
                                      'checkpoint-{epoch}.h5')
            callbacks.append(keras.callbacks.ModelCheckpoint(checkpoint))
            callbacks.append(keras.callbacks.TensorBoard(log_dir=tensorboard_dir))
            verbose = 2

        # Fit the model on the batches generated by datagen.flow().
        model.fit_generator(datagen.flow(x_train, y_train,
                                        batch_size=batch_size),
                            steps_per_epoch=x_train.shape[0] // batch_size,
                            epochs=epochs,
                            verbose=verbose,
                            callbacks=callbacks,
                            validation_data=(x_test, y_test))

        # Evaluate model with test data set and share sample prediction results
        evaluation = hvd.allreduce(model.evaluate_generator(datagen.flow(x_test, y_test,
                                                                         batch_size=batch_size),
                                                            steps=x_test.shape[0] // batch_size))
        if hvd.rank() == 0:
            print('Model Accuracy = %.2f' % (evaluation[1]))
            riseml.report_result(accuracy=float(evaluation[1]))


def save_model(model, save_dir, model_name='keras_model.h5'):
    # Save model and weights
    if not os.path.isdir(save_dir):
        os.makedirs(save_dir)
    model_path = os.path.join(save_dir, model_name)
    model.save(model_path)
    print('Saved trained model at %s ' % model_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train on CIFAR-10.')
    parser.add_argument('data', type=str,
                        nargs='?',
                        help='path to CIFAR-10 data')
    parser.add_argument('--lr', type=float,
                        default=0.0001,
                        help='learning rate')
    parser.add_argument('--lr-decay', type=float,
                        default=1e-6,
                        help='learning rate decay')
    parser.add_argument('--epochs', type=int,
                        default=20,
                        help='number of epochs to train')
    parser.add_argument('--augment-data', type=bool,
                        default=True,
                        help='Whether to augment data')
    args = parser.parse_args()
    tensorboard_dir = os.environ.get('OUTPUT_DIR', 'tensorboard')

    # Horovod: initialize Horovod.
    hvd.init()

    # Horovod: pin GPU to be used to process local rank (one GPU per process)
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    config.gpu_options.visible_device_list = str(hvd.local_rank())
    K.set_session(tf.Session(config=config))

    if args.data is None:
        xy_train, xy_test = download_data()
    else:
        xy_train, xy_test = get_data(args.data)
    input_shape = xy_train[0].shape[1:]
    model = get_model(input_shape, args.lr, args.lr_decay)
    print('Learning rate: %s' % (args.lr))
    print('Learning rate decay: %s' % (args.lr_decay))
    train_model(model, xy_train, xy_test, tensorboard_dir,
                epochs=args.epochs,
                data_augmentation=args.augment_data)

    # Horovod: save checkpoints only on worker 0 to prevent other workers from corrupting them.
    if hvd.rank() == 0:
        save_model(model, OUTPUT_DIR)
