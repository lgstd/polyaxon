# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import tensorflow as tf

import polyaxon as plx
from polyaxon.datasets import mnist


def create_experiment_json_fn(output_dir):
    """Creates an experiment using cnn for MNIST dataset classification task.

    References:
        * Y. LeCun, L. Bottou, Y. Bengio, and P. Haffner. "Gradient-based learning applied to
        document recognition." Proceedings of the IEEE, 86(11):2278-2324, November 1998.
    Links:
        * [MNIST Dataset] http://yann.lecun.com/exdb/mnist/
    """
    dataset_dir = './data/mnist'
    mnist.prepare(dataset_dir)
    train_data_file = mnist.RECORD_FILE_NAME_FORMAT.format(dataset_dir, plx.Modes.TRAIN)
    eval_data_file = mnist.RECORD_FILE_NAME_FORMAT.format(dataset_dir, plx.Modes.EVAL)
    meta_data_file = mnist.MEAT_DATA_FILENAME_FORMAT.format(dataset_dir)

    config = {
        'name': 'conv_mnsit',
        'output_dir': output_dir,
        'eval_every_n_steps': 5,
        'run_config': {'save_checkpoints_steps': 100},
        'train_input_data_config': {
            'pipeline_config': {'module': 'TFRecordImagePipeline', 'batch_size': 64,
                                'num_epochs': 5,
                                'shuffle': True, 'dynamic_pad': False,
                                'params': {'data_files': train_data_file,
                                           'meta_data_file': meta_data_file}},
        },
        'eval_input_data_config': {
            'pipeline_config': {'module': 'TFRecordImagePipeline', 'batch_size': 32,
                                'num_epochs': 1,
                                'shuffle': True, 'dynamic_pad': False,
                                'params': {'data_files': eval_data_file,
                                           'meta_data_file': meta_data_file}},
        },
        'estimator_config': {'output_dir': output_dir},
        'model_config': {
            'module': 'Classifier',
            'loss_config': {'module': 'sigmoid_cross_entropy'},
            'eval_metrics_config': [{'module': 'streaming_accuracy'}],
            'optimizer_config': {'module': 'adam', 'learning_rate': 0.001},
            'one_hot_encode': True,
            'n_classes': 10,
            'graph_config': {
                'name': 'convnet',
                'features': ['image'],
                'definition': [
                    ('Conv2d',
                     {'num_filter': 32, 'filter_size': 3, 'strides': 1, 'activation': 'elu',
                      'regularizer': 'l2_regularizer'}),
                    ('MaxPool2d', {'kernel_size': 2}),
                    ('LocalResponseNormalization', {}),
                    ('Conv2d', {'num_filter': 64, 'filter_size': 3, 'activation': 'relu',
                                'regularizer': 'l2_regularizer'}),
                    ('MaxPool2d', {'kernel_size': 2}),
                    ('LocalResponseNormalization', {}),
                    ('FullyConnected', {'num_units': 128, 'activation': 'tanh'}),
                    ('Dropout', {'keep_prob': 0.8}),
                    ('FullyConnected', {'num_units': 256, 'activation': 'tanh'}),
                    ('Dropout', {'keep_prob': 0.8}),
                    ('FullyConnected', {'num_units': 10}),
                ]
            }
        }
    }
    experiment_config = plx.configs.ExperimentConfig.read_configs(config)
    return plx.experiments.create_experiment(experiment_config)


def main(*args):
    plx.experiments.run_experiment(experiment_fn=create_experiment_json_fn,
                                   output_dir="/tmp/polyaxon_logs/conv_mnsit",
                                   schedule='continuous_train_and_evaluate')


if __name__ == "__main__":
    tf.logging.set_verbosity(tf.logging.INFO)
    tf.app.run()
