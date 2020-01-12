import keras
from keras.models import Model
from keras import layers
import keras.backend as K
import numpy as np
from keras.layers.core import Lambda
import tensorflow as tf


weights_dict = dict()
def load_weights_from_file(weight_file):
    try:
        weights_dict = np.load(weight_file).item()
    except:
        weights_dict = np.load(weight_file, encoding='bytes').item()

    return weights_dict


def set_layer_weights(model, weights_dict):
    for layer in model.layers:
        if layer.name in weights_dict:
            cur_dict = weights_dict[layer.name]
            current_layer_parameters = list()
            if layer.__class__.__name__ == "BatchNormalization":
                if 'scale' in cur_dict:
                    current_layer_parameters.append(cur_dict['scale'])
                if 'bias' in cur_dict:
                    current_layer_parameters.append(cur_dict['bias'])
                current_layer_parameters.extend([cur_dict['mean'], cur_dict['var']])
            elif layer.__class__.__name__ == "Scale":
                if 'scale' in cur_dict:
                    current_layer_parameters.append(cur_dict['scale'])
                if 'bias' in cur_dict:
                    current_layer_parameters.append(cur_dict['bias'])
            elif layer.__class__.__name__ == "SeparableConv2D":
                current_layer_parameters = [cur_dict['depthwise_filter'], cur_dict['pointwise_filter']]
                if 'bias' in cur_dict:
                    current_layer_parameters.append(cur_dict['bias'])
            elif layer.__class__.__name__ == "Embedding":
                current_layer_parameters.append(cur_dict['weights'])
            else:
                # rot weights
                current_layer_parameters = [cur_dict['weights']]
                if 'bias' in cur_dict:
                    current_layer_parameters.append(cur_dict['bias'])
            model.get_layer(layer.name).set_weights(current_layer_parameters)

    return model


def KitModel(weight_file = None):
    global weights_dict
    weights_dict = load_weights_from_file(weight_file) if not weight_file == None else None
        
    input_1         = layers.Input(name = 'input_1', shape = (224, 224, 3,) , dtype = 'float32')
    conv1_pad       = layers.ZeroPadding2D(name='conv1_pad', padding=((3, 3), (3, 3)))(input_1)
    conv1           = convolution(weights_dict, name='conv1', input=conv1_pad, group=1, conv_type='layers.Conv2D', filters=64, kernel_size=(7, 7), strides=(2, 2), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn_conv1        = layers.BatchNormalization(name = 'bn_conv1', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(conv1)
    activation_1    = layers.Activation(name='activation_1', activation='relu')(bn_conv1)
    pool1_pad       = layers.ZeroPadding2D(name='pool1_pad', padding=((1, 1), (1, 1)))(activation_1)
    max_pooling2d_1 = layers.MaxPooling2D(name = 'max_pooling2d_1', pool_size = (3, 3), strides = (2, 2), padding = 'valid')(pool1_pad)
    res2a_branch2a  = convolution(weights_dict, name='res2a_branch2a', input=max_pooling2d_1, group=1, conv_type='layers.Conv2D', filters=64, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    res2a_branch1   = convolution(weights_dict, name='res2a_branch1', input=max_pooling2d_1, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn2a_branch2a   = layers.BatchNormalization(name = 'bn2a_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2a_branch2a)
    bn2a_branch1    = layers.BatchNormalization(name = 'bn2a_branch1', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2a_branch1)
    activation_2    = layers.Activation(name='activation_2', activation='relu')(bn2a_branch2a)
    res2a_branch2b  = convolution(weights_dict, name='res2a_branch2b', input=activation_2, group=1, conv_type='layers.Conv2D', filters=64, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn2a_branch2b   = layers.BatchNormalization(name = 'bn2a_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2a_branch2b)
    activation_3    = layers.Activation(name='activation_3', activation='relu')(bn2a_branch2b)
    res2a_branch2c  = convolution(weights_dict, name='res2a_branch2c', input=activation_3, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn2a_branch2c   = layers.BatchNormalization(name = 'bn2a_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2a_branch2c)
    add_1           = my_add()([bn2a_branch2c, bn2a_branch1])
    activation_4    = layers.Activation(name='activation_4', activation='relu')(add_1)
    res2b_branch2a  = convolution(weights_dict, name='res2b_branch2a', input=activation_4, group=1, conv_type='layers.Conv2D', filters=64, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn2b_branch2a   = layers.BatchNormalization(name = 'bn2b_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2b_branch2a)
    activation_5    = layers.Activation(name='activation_5', activation='relu')(bn2b_branch2a)
    res2b_branch2b  = convolution(weights_dict, name='res2b_branch2b', input=activation_5, group=1, conv_type='layers.Conv2D', filters=64, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn2b_branch2b   = layers.BatchNormalization(name = 'bn2b_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2b_branch2b)
    activation_6    = layers.Activation(name='activation_6', activation='relu')(bn2b_branch2b)
    res2b_branch2c  = convolution(weights_dict, name='res2b_branch2c', input=activation_6, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn2b_branch2c   = layers.BatchNormalization(name = 'bn2b_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2b_branch2c)
    add_2           = my_add()([bn2b_branch2c, activation_4])
    activation_7    = layers.Activation(name='activation_7', activation='relu')(add_2)
    res2c_branch2a  = convolution(weights_dict, name='res2c_branch2a', input=activation_7, group=1, conv_type='layers.Conv2D', filters=64, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn2c_branch2a   = layers.BatchNormalization(name = 'bn2c_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2c_branch2a)
    activation_8    = layers.Activation(name='activation_8', activation='relu')(bn2c_branch2a)
    res2c_branch2b  = convolution(weights_dict, name='res2c_branch2b', input=activation_8, group=1, conv_type='layers.Conv2D', filters=64, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn2c_branch2b   = layers.BatchNormalization(name = 'bn2c_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2c_branch2b)
    activation_9    = layers.Activation(name='activation_9', activation='relu')(bn2c_branch2b)
    res2c_branch2c  = convolution(weights_dict, name='res2c_branch2c', input=activation_9, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn2c_branch2c   = layers.BatchNormalization(name = 'bn2c_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res2c_branch2c)
    add_3           = my_add()([bn2c_branch2c, activation_7])
    activation_10   = layers.Activation(name='activation_10', activation='relu')(add_3)
    res3a_branch2a  = convolution(weights_dict, name='res3a_branch2a', input=activation_10, group=1, conv_type='layers.Conv2D', filters=128, kernel_size=(1, 1), strides=(2, 2), dilation_rate=(1, 1), padding='valid', use_bias=True)
    res3a_branch1   = convolution(weights_dict, name='res3a_branch1', input=activation_10, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(1, 1), strides=(2, 2), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn3a_branch2a   = layers.BatchNormalization(name = 'bn3a_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3a_branch2a)
    bn3a_branch1    = layers.BatchNormalization(name = 'bn3a_branch1', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3a_branch1)
    activation_11   = layers.Activation(name='activation_11', activation='relu')(bn3a_branch2a)
    res3a_branch2b  = convolution(weights_dict, name='res3a_branch2b', input=activation_11, group=1, conv_type='layers.Conv2D', filters=128, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn3a_branch2b   = layers.BatchNormalization(name = 'bn3a_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3a_branch2b)
    activation_12   = layers.Activation(name='activation_12', activation='relu')(bn3a_branch2b)
    res3a_branch2c  = convolution(weights_dict, name='res3a_branch2c', input=activation_12, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn3a_branch2c   = layers.BatchNormalization(name = 'bn3a_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3a_branch2c)
    add_4           = my_add()([bn3a_branch2c, bn3a_branch1])
    activation_13   = layers.Activation(name='activation_13', activation='relu')(add_4)
    res3b_branch2a  = convolution(weights_dict, name='res3b_branch2a', input=activation_13, group=1, conv_type='layers.Conv2D', filters=128, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn3b_branch2a   = layers.BatchNormalization(name = 'bn3b_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3b_branch2a)
    activation_14   = layers.Activation(name='activation_14', activation='relu')(bn3b_branch2a)
    res3b_branch2b  = convolution(weights_dict, name='res3b_branch2b', input=activation_14, group=1, conv_type='layers.Conv2D', filters=128, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn3b_branch2b   = layers.BatchNormalization(name = 'bn3b_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3b_branch2b)
    activation_15   = layers.Activation(name='activation_15', activation='relu')(bn3b_branch2b)
    res3b_branch2c  = convolution(weights_dict, name='res3b_branch2c', input=activation_15, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn3b_branch2c   = layers.BatchNormalization(name = 'bn3b_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3b_branch2c)
    add_5           = my_add()([bn3b_branch2c, activation_13])
    activation_16   = layers.Activation(name='activation_16', activation='relu')(add_5)
    res3c_branch2a  = convolution(weights_dict, name='res3c_branch2a', input=activation_16, group=1, conv_type='layers.Conv2D', filters=128, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn3c_branch2a   = layers.BatchNormalization(name = 'bn3c_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3c_branch2a)
    activation_17   = layers.Activation(name='activation_17', activation='relu')(bn3c_branch2a)
    res3c_branch2b  = convolution(weights_dict, name='res3c_branch2b', input=activation_17, group=1, conv_type='layers.Conv2D', filters=128, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn3c_branch2b   = layers.BatchNormalization(name = 'bn3c_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3c_branch2b)
    activation_18   = layers.Activation(name='activation_18', activation='relu')(bn3c_branch2b)
    res3c_branch2c  = convolution(weights_dict, name='res3c_branch2c', input=activation_18, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn3c_branch2c   = layers.BatchNormalization(name = 'bn3c_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3c_branch2c)
    add_6           = my_add()([bn3c_branch2c, activation_16])
    activation_19   = layers.Activation(name='activation_19', activation='relu')(add_6)
    res3d_branch2a  = convolution(weights_dict, name='res3d_branch2a', input=activation_19, group=1, conv_type='layers.Conv2D', filters=128, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn3d_branch2a   = layers.BatchNormalization(name = 'bn3d_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3d_branch2a)
    activation_20   = layers.Activation(name='activation_20', activation='relu')(bn3d_branch2a)
    res3d_branch2b  = convolution(weights_dict, name='res3d_branch2b', input=activation_20, group=1, conv_type='layers.Conv2D', filters=128, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn3d_branch2b   = layers.BatchNormalization(name = 'bn3d_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3d_branch2b)
    activation_21   = layers.Activation(name='activation_21', activation='relu')(bn3d_branch2b)
    res3d_branch2c  = convolution(weights_dict, name='res3d_branch2c', input=activation_21, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn3d_branch2c   = layers.BatchNormalization(name = 'bn3d_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res3d_branch2c)
    add_7           = my_add()([bn3d_branch2c, activation_19])
    activation_22   = layers.Activation(name='activation_22', activation='relu')(add_7)
    res4a_branch2a  = convolution(weights_dict, name='res4a_branch2a', input=activation_22, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(2, 2), dilation_rate=(1, 1), padding='valid', use_bias=True)
    res4a_branch1   = convolution(weights_dict, name='res4a_branch1', input=activation_22, group=1, conv_type='layers.Conv2D', filters=1024, kernel_size=(1, 1), strides=(2, 2), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4a_branch2a   = layers.BatchNormalization(name = 'bn4a_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4a_branch2a)
    bn4a_branch1    = layers.BatchNormalization(name = 'bn4a_branch1', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4a_branch1)
    activation_23   = layers.Activation(name='activation_23', activation='relu')(bn4a_branch2a)
    res4a_branch2b  = convolution(weights_dict, name='res4a_branch2b', input=activation_23, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn4a_branch2b   = layers.BatchNormalization(name = 'bn4a_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4a_branch2b)
    activation_24   = layers.Activation(name='activation_24', activation='relu')(bn4a_branch2b)
    res4a_branch2c  = convolution(weights_dict, name='res4a_branch2c', input=activation_24, group=1, conv_type='layers.Conv2D', filters=1024, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4a_branch2c   = layers.BatchNormalization(name = 'bn4a_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4a_branch2c)
    add_8           = my_add()([bn4a_branch2c, bn4a_branch1])
    activation_25   = layers.Activation(name='activation_25', activation='relu')(add_8)
    res4b_branch2a  = convolution(weights_dict, name='res4b_branch2a', input=activation_25, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4b_branch2a   = layers.BatchNormalization(name = 'bn4b_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4b_branch2a)
    activation_26   = layers.Activation(name='activation_26', activation='relu')(bn4b_branch2a)
    res4b_branch2b  = convolution(weights_dict, name='res4b_branch2b', input=activation_26, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn4b_branch2b   = layers.BatchNormalization(name = 'bn4b_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4b_branch2b)
    activation_27   = layers.Activation(name='activation_27', activation='relu')(bn4b_branch2b)
    res4b_branch2c  = convolution(weights_dict, name='res4b_branch2c', input=activation_27, group=1, conv_type='layers.Conv2D', filters=1024, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4b_branch2c   = layers.BatchNormalization(name = 'bn4b_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4b_branch2c)
    add_9           = my_add()([bn4b_branch2c, activation_25])
    activation_28   = layers.Activation(name='activation_28', activation='relu')(add_9)
    res4c_branch2a  = convolution(weights_dict, name='res4c_branch2a', input=activation_28, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4c_branch2a   = layers.BatchNormalization(name = 'bn4c_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4c_branch2a)
    activation_29   = layers.Activation(name='activation_29', activation='relu')(bn4c_branch2a)
    res4c_branch2b  = convolution(weights_dict, name='res4c_branch2b', input=activation_29, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn4c_branch2b   = layers.BatchNormalization(name = 'bn4c_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4c_branch2b)
    activation_30   = layers.Activation(name='activation_30', activation='relu')(bn4c_branch2b)
    res4c_branch2c  = convolution(weights_dict, name='res4c_branch2c', input=activation_30, group=1, conv_type='layers.Conv2D', filters=1024, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4c_branch2c   = layers.BatchNormalization(name = 'bn4c_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4c_branch2c)
    add_10          = my_add()([bn4c_branch2c, activation_28])
    activation_31   = layers.Activation(name='activation_31', activation='relu')(add_10)
    res4d_branch2a  = convolution(weights_dict, name='res4d_branch2a', input=activation_31, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4d_branch2a   = layers.BatchNormalization(name = 'bn4d_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4d_branch2a)
    activation_32   = layers.Activation(name='activation_32', activation='relu')(bn4d_branch2a)
    res4d_branch2b  = convolution(weights_dict, name='res4d_branch2b', input=activation_32, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn4d_branch2b   = layers.BatchNormalization(name = 'bn4d_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4d_branch2b)
    activation_33   = layers.Activation(name='activation_33', activation='relu')(bn4d_branch2b)
    res4d_branch2c  = convolution(weights_dict, name='res4d_branch2c', input=activation_33, group=1, conv_type='layers.Conv2D', filters=1024, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4d_branch2c   = layers.BatchNormalization(name = 'bn4d_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4d_branch2c)
    add_11          = my_add()([bn4d_branch2c, activation_31])
    activation_34   = layers.Activation(name='activation_34', activation='relu')(add_11)
    res4e_branch2a  = convolution(weights_dict, name='res4e_branch2a', input=activation_34, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4e_branch2a   = layers.BatchNormalization(name = 'bn4e_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4e_branch2a)
    activation_35   = layers.Activation(name='activation_35', activation='relu')(bn4e_branch2a)
    res4e_branch2b  = convolution(weights_dict, name='res4e_branch2b', input=activation_35, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn4e_branch2b   = layers.BatchNormalization(name = 'bn4e_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4e_branch2b)
    activation_36   = layers.Activation(name='activation_36', activation='relu')(bn4e_branch2b)
    res4e_branch2c  = convolution(weights_dict, name='res4e_branch2c', input=activation_36, group=1, conv_type='layers.Conv2D', filters=1024, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4e_branch2c   = layers.BatchNormalization(name = 'bn4e_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4e_branch2c)
    add_12          = my_add()([bn4e_branch2c, activation_34])
    activation_37   = layers.Activation(name='activation_37', activation='relu')(add_12)
    res4f_branch2a  = convolution(weights_dict, name='res4f_branch2a', input=activation_37, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4f_branch2a   = layers.BatchNormalization(name = 'bn4f_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4f_branch2a)
    activation_38   = layers.Activation(name='activation_38', activation='relu')(bn4f_branch2a)
    res4f_branch2b  = convolution(weights_dict, name='res4f_branch2b', input=activation_38, group=1, conv_type='layers.Conv2D', filters=256, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn4f_branch2b   = layers.BatchNormalization(name = 'bn4f_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4f_branch2b)
    activation_39   = layers.Activation(name='activation_39', activation='relu')(bn4f_branch2b)
    res4f_branch2c  = convolution(weights_dict, name='res4f_branch2c', input=activation_39, group=1, conv_type='layers.Conv2D', filters=1024, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn4f_branch2c   = layers.BatchNormalization(name = 'bn4f_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res4f_branch2c)
    add_13          = my_add()([bn4f_branch2c, activation_37])
    activation_40   = layers.Activation(name='activation_40', activation='relu')(add_13)
    res5a_branch2a  = convolution(weights_dict, name='res5a_branch2a', input=activation_40, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(1, 1), strides=(2, 2), dilation_rate=(1, 1), padding='valid', use_bias=True)
    res5a_branch1   = convolution(weights_dict, name='res5a_branch1', input=activation_40, group=1, conv_type='layers.Conv2D', filters=2048, kernel_size=(1, 1), strides=(2, 2), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn5a_branch2a   = layers.BatchNormalization(name = 'bn5a_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5a_branch2a)
    bn5a_branch1    = layers.BatchNormalization(name = 'bn5a_branch1', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5a_branch1)
    activation_41   = layers.Activation(name='activation_41', activation='relu')(bn5a_branch2a)
    res5a_branch2b  = convolution(weights_dict, name='res5a_branch2b', input=activation_41, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn5a_branch2b   = layers.BatchNormalization(name = 'bn5a_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5a_branch2b)
    activation_42   = layers.Activation(name='activation_42', activation='relu')(bn5a_branch2b)
    res5a_branch2c  = convolution(weights_dict, name='res5a_branch2c', input=activation_42, group=1, conv_type='layers.Conv2D', filters=2048, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn5a_branch2c   = layers.BatchNormalization(name = 'bn5a_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5a_branch2c)
    add_14          = my_add()([bn5a_branch2c, bn5a_branch1])
    activation_43   = layers.Activation(name='activation_43', activation='relu')(add_14)
    res5b_branch2a  = convolution(weights_dict, name='res5b_branch2a', input=activation_43, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn5b_branch2a   = layers.BatchNormalization(name = 'bn5b_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5b_branch2a)
    activation_44   = layers.Activation(name='activation_44', activation='relu')(bn5b_branch2a)
    res5b_branch2b  = convolution(weights_dict, name='res5b_branch2b', input=activation_44, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn5b_branch2b   = layers.BatchNormalization(name = 'bn5b_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5b_branch2b)
    activation_45   = layers.Activation(name='activation_45', activation='relu')(bn5b_branch2b)
    res5b_branch2c  = convolution(weights_dict, name='res5b_branch2c', input=activation_45, group=1, conv_type='layers.Conv2D', filters=2048, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn5b_branch2c   = layers.BatchNormalization(name = 'bn5b_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5b_branch2c)
    add_15          = my_add()([bn5b_branch2c, activation_43])
    activation_46   = layers.Activation(name='activation_46', activation='relu')(add_15)
    res5c_branch2a  = convolution(weights_dict, name='res5c_branch2a', input=activation_46, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn5c_branch2a   = layers.BatchNormalization(name = 'bn5c_branch2a', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5c_branch2a)
    activation_47   = layers.Activation(name='activation_47', activation='relu')(bn5c_branch2a)
    res5c_branch2b  = convolution(weights_dict, name='res5c_branch2b', input=activation_47, group=1, conv_type='layers.Conv2D', filters=512, kernel_size=(3, 3), strides=(1, 1), dilation_rate=(1, 1), padding='same', use_bias=True)
    bn5c_branch2b   = layers.BatchNormalization(name = 'bn5c_branch2b', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5c_branch2b)
    activation_48   = layers.Activation(name='activation_48', activation='relu')(bn5c_branch2b)
    res5c_branch2c  = convolution(weights_dict, name='res5c_branch2c', input=activation_48, group=1, conv_type='layers.Conv2D', filters=2048, kernel_size=(1, 1), strides=(1, 1), dilation_rate=(1, 1), padding='valid', use_bias=True)
    bn5c_branch2c   = layers.BatchNormalization(name = 'bn5c_branch2c', axis = 3, epsilon = 0.0010000000474974513, center = True, scale = True)(res5c_branch2c)
    add_16          = my_add()([bn5c_branch2c, activation_46])
    activation_49   = layers.Activation(name='activation_49', activation='relu')(add_16)
    avg_pool        = layers.GlobalAveragePooling2D(name = 'avg_pool')(activation_49)
    avg_pool_flatten = __flatten(name = 'avg_pool_flatten', input = avg_pool)
    fc1000          = layers.Dense(name = 'fc1000', units = 1000, use_bias = True)(avg_pool_flatten)
    fc1000_activation = layers.Activation(name='fc1000_activation', activation='softmax')(fc1000)
    model           = Model(inputs = [input_1], outputs = [fc1000_activation])
    set_layer_weights(model, weights_dict)
    return model

def __flatten(name, input):
    if input.shape.ndims > 2: return layers.Flatten(name = name)(input)
    else: return input


class my_add(keras.layers.Layer):
    def __init__(self, **kwargs):
        super(my_add, self).__init__(**kwargs)
    def call(self, inputs):
        res = inputs[0] + inputs[1]
        self.output_shapes = K.int_shape(res)
        return res
    
    def compute_output_shape(self, input_shape):
        return self.output_shapes


def convolution(weights_dict, name, input, group, conv_type, filters=None, **kwargs):
    if not conv_type.startswith('layer'):
        layer = keras.applications.mobilenet.DepthwiseConv2D(name=name, **kwargs)(input)
        return layer
    elif conv_type == 'layers.DepthwiseConv2D':
        layer = layers.DepthwiseConv2D(name=name, **kwargs)(input)
        return layer
    
    inp_filters = K.int_shape(input)[-1]
    inp_grouped_channels = int(inp_filters / group)
    out_grouped_channels = int(filters / group)
    group_list = []
    if group == 1:
        func = getattr(layers, conv_type.split('.')[-1])
        layer = func(name = name, filters = filters, **kwargs)(input)
        return layer
    weight_groups = list()
    if not weights_dict == None:
        w = np.array(weights_dict[name]['weights'])
        weight_groups = np.split(w, indices_or_sections=group, axis=-1)
    for c in range(group):
        x = layers.Lambda(lambda z: z[..., c * inp_grouped_channels:(c + 1) * inp_grouped_channels])(input)
        x = layers.Conv2D(name=name + "_" + str(c), filters=out_grouped_channels, **kwargs)(x)
        weights_dict[name + "_" + str(c)] = dict()
        weights_dict[name + "_" + str(c)]['weights'] = weight_groups[c]
        group_list.append(x)
    layer = layers.concatenate(group_list, axis = -1)
    if 'bias' in weights_dict[name]:
        b = K.variable(weights_dict[name]['bias'], name = name + "_bias")
        layer = layer + b
    return layer

