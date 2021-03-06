# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import tensorflow as tf

import polyaxon as plx
from polyaxon.datasets import mnist


def create_experiment_json_fn(output_dir):
    """Creates an experiment using cnn for MNIST dataset classification task."""

    dataset_dir = './data/mnist'
    mnist.prepare(dataset_dir)
    train_data_file = mnist.RECORD_FILE_NAME_FORMAT.format(dataset_dir, plx.Modes.TRAIN)
    eval_data_file = mnist.RECORD_FILE_NAME_FORMAT.format(dataset_dir, plx.Modes.EVAL)
    meta_data_file = mnist.MEAT_DATA_FILENAME_FORMAT.format(dataset_dir)

    config = {
        'name': 'conv_highway',
        'output_dir': output_dir,
        'eval_every_n_steps': 5,
        'run_config': {'save_checkpoints_steps': 100},
        'train_input_data_config': {
            'pipeline_config': {'module': 'TFRecordImagePipeline', 'batch_size': 64, 'num_epochs': 5,
                                'shuffle': True, 'dynamic_pad': False,
                                'params': {'data_files': train_data_file,
                                           'meta_data_file': meta_data_file}},
        },
        'eval_input_data_config': {
            'pipeline_config': {'module': 'TFRecordImagePipeline', 'batch_size': 32, 'num_epochs': 1,
                                'shuffle': True, 'dynamic_pad': False,
                                'params': {'data_files': eval_data_file,
                                           'meta_data_file': meta_data_file}},
        },
        'estimator_config': {'output_dir': output_dir},
        'model_config': {
            'module': 'Classifier',
            'loss_config': {'module': 'softmax_cross_entropy'},
            'eval_metrics_config': [{'module': 'streaming_accuracy'}],
            'optimizer_config': {'module': 'adam', 'learning_rate': 0.001},
            'one_hot_encode': True,
            'n_classes': 10,
            'graph_config': {
                'name': 'mnist',
                'features': ['image'],
                'definition': [
                    (plx.layers.HighwayConv2d,
                     {'num_filter': 32, 'filter_size': 3, 'strides': 1, 'activation': 'elu'}),
                    (plx.layers.HighwayConv2d,
                     {'num_filter': 16, 'filter_size': 2, 'strides': 1, 'activation': 'elu'}),
                    (plx.layers.HighwayConv2d,
                     {'num_filter': 16, 'filter_size': 1, 'strides': 1, 'activation': 'elu'}),
                    (plx.layers.MaxPool2d, {'kernel_size': 2}),
                    (plx.layers.BatchNormalization, {}),
                    (plx.layers.FullyConnected, {'num_units': 128, 'activation': 'elu'}),
                    (plx.layers.FullyConnected, {'num_units': 256, 'activation': 'elu'}),
                    (plx.layers.FullyConnected, {'num_units': 10}),
                ]
            }
        }
    }
    experiment_config = plx.configs.ExperimentConfig.read_configs(config)
    return plx.experiments.create_experiment(experiment_config)


def main(*args):
    plx.experiments.run_experiment(experiment_fn=create_experiment_json_fn,
                                   output_dir="/tmp/polyaxon_logs/conv_highway_mnsit",
                                   schedule='continuous_train_and_evaluate')


if __name__ == "__main__":
    tf.logging.set_verbosity(tf.logging.INFO)
    tf.app.run()
