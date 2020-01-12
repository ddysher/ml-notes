'''Trains a simple deep NN on the MNIST dataset.

Gets to 98.40% test accuracy after 20 epochs
(there is *a lot* of margin for parameter tuning).
2 seconds per epoch on a K520 GPU.
'''

from __future__ import print_function

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import RMSprop

batch_size = 128
num_classes = 10
epochs = 20

# The data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Convert x_train.shape from (60000,28,28) to (6000, 784), similar
# transformation applies to x_test.
x_train = x_train.reshape(60000, 784)
x_test = x_test.reshape(10000, 784)

# Convert x_train.dtype from 'uint8' to 'float32'.
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')

# Convert data points to [0,1].
x_train /= 255
x_test /= 255

print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# Convert class vectors to binary class matrices (to be used
# with categorical_crossentropy.
#
# From:
#   y_train: array([5, 0, 4, ..., 5, 6, 8], dtype=uint8)
# To:
#   array([[0., 0., 0., ..., 0., 0., 0.],
#          [1., 0., 0., ..., 0., 0., 0.],
#          [0., 0., 0., ..., 0., 0., 0.],
#          ...,
#          [0., 0., 0., ..., 0., 0., 0.],
#          [0., 0., 0., ..., 0., 0., 0.],
#          [0., 0., 0., ..., 0., 1., 0.]], dtype=float32)
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

# 1. create a sequential model
# 2. the model will take as input arrays of shape (*, 784) and output arrays of shape (*, 512).
# 3. apply adropout with 0.2 probability
# 4. add another dense layer with 512 output dimension
# 5. apply adropout with 0.2 probability
# 5. add 'softmax'
model = Sequential()
model.add(Dense(512, activation='relu', input_shape=(784,)))
model.add(Dropout(0.2))
model.add(Dense(512, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(num_classes, activation='softmax'))

# _________________________________________________________________
# Layer (type)                 Output Shape              Param #
# =================================================================
# dense_1 (Dense)              (None, 512)               401920    <-- (784+1)*512
# _________________________________________________________________
# dropout_1 (Dropout)          (None, 512)               0
# _________________________________________________________________
# dense_2 (Dense)              (None, 512)               262656    <-- (512+1)*512
# _________________________________________________________________
# dropout_2 (Dropout)          (None, 512)               0
# _________________________________________________________________
# dense_3 (Dense)              (None, 10)                5130      <-- (512+1)*10
# =================================================================
# Total params: 669,706
# Trainable params: 669,706
# Non-trainable params: 0
# _________________________________________________________________
model.summary()

# Configures the model for training (similar to 'add layer'). For loss, we
# can also use keras.losses.categorical_crossentropy directly.
model.compile(loss='categorical_crossentropy',
              optimizer=RMSprop(),
              metrics=['accuracy'])

# Epoch 1/20
# 60000/60000 [==============================] - 5s 83us/step - loss: 0.2469 - acc: 0.9242 - val_loss: 0.1083 - val_acc: 0.9671
# Epoch 2/20
# 60000/60000 [==============================] - 5s 78us/step - loss: 0.1021 - acc: 0.9690 - val_loss: 0.0936 - val_acc: 0.9731
# Epoch 3/20
# 60000/60000 [==============================] - 5s 78us/step - loss: 0.0764 - acc: 0.9763 - val_loss: 0.1103 - val_acc: 0.9681
# Epoch 4/20
# 60000/60000 [==============================] - 5s 79us/step - loss: 0.0619 - acc: 0.9816 - val_loss: 0.0891 - val_acc: 0.9781
# Epoch 5/20
# 60000/60000 [==============================] - 5s 80us/step - loss: 0.0514 - acc: 0.9838 - val_loss: 0.0780 - val_acc: 0.9783
# Epoch 6/20
# 60000/60000 [==============================] - 5s 82us/step - loss: 0.0469 - acc: 0.9860 - val_loss: 0.0768 - val_acc: 0.9815
# Epoch 7/20
# 60000/60000 [==============================] - 5s 79us/step - loss: 0.0383 - acc: 0.9888 - val_loss: 0.0876 - val_acc: 0.9796
# Epoch 8/20
# 60000/60000 [==============================] - 5s 78us/step - loss: 0.0353 - acc: 0.9897 - val_loss: 0.0875 - val_acc: 0.9805
# Epoch 9/20
# 60000/60000 [==============================] - 5s 78us/step - loss: 0.0341 - acc: 0.9898 - val_loss: 0.0880 - val_acc: 0.9821
# Epoch 10/20
# 60000/60000 [==============================] - 5s 77us/step - loss: 0.0318 - acc: 0.9909 - val_loss: 0.0907 - val_acc: 0.9826
# Epoch 11/20
# 60000/60000 [==============================] - 5s 77us/step - loss: 0.0281 - acc: 0.9917 - val_loss: 0.0913 - val_acc: 0.9814
# Epoch 12/20
# 60000/60000 [==============================] - 5s 80us/step - loss: 0.0259 - acc: 0.9930 - val_loss: 0.0949 - val_acc: 0.9827
# Epoch 13/20
# 60000/60000 [==============================] - 5s 78us/step - loss: 0.0247 - acc: 0.9932 - val_loss: 0.1066 - val_acc: 0.9823
# Epoch 14/20
# 60000/60000 [==============================] - 5s 78us/step - loss: 0.0249 - acc: 0.9934 - val_loss: 0.1086 - val_acc: 0.9812
# Epoch 15/20
# 60000/60000 [==============================] - 5s 77us/step - loss: 0.0241 - acc: 0.9935 - val_loss: 0.0969 - val_acc: 0.9835
# Epoch 16/20
# 60000/60000 [==============================] - 5s 82us/step - loss: 0.0215 - acc: 0.9946 - val_loss: 0.1101 - val_acc: 0.9819
# Epoch 17/20
# 60000/60000 [==============================] - 6s 94us/step - loss: 0.0216 - acc: 0.9942 - val_loss: 0.1053 - val_acc: 0.9839
# Epoch 18/20
# 60000/60000 [==============================] - 5s 89us/step - loss: 0.0200 - acc: 0.9948 - val_loss: 0.1157 - val_acc: 0.9827
# Epoch 19/20
# 60000/60000 [==============================] - 6s 94us/step - loss: 0.0189 - acc: 0.9953 - val_loss: 0.0994 - val_acc: 0.9845
# Epoch 20/20
# 60000/60000 [==============================] - 5s 91us/step - loss: 0.0177 - acc: 0.9954 - val_loss: 0.0998 - val_acc: 0.9851
#
# The history object contains arrays for loss, acc, val_loss, val_acc.
history = model.fit(x_train, y_train,
                    batch_size=batch_size,
                    epochs=epochs,
                    verbose=1,
                    validation_data=(x_test, y_test))

# Returns the loss value & metrics values for the model in test mode.
score = model.evaluate(x_test, y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])
