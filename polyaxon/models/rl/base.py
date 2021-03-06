# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from collections import Mapping

import tensorflow as tf

from tensorflow.python.estimator.model_fn import EstimatorSpec
from tensorflow.python.training import training

from polyaxon.layers import FullyConnected
from polyaxon.libs import getters
from polyaxon.libs.utils import get_tensor_batch_size
from polyaxon.libs.template_module import FunctionModule
from polyaxon.models import BaseModel


class RLBaseModel(BaseModel):
    """Base reinforcement learning model class.

    Args:
        mode: `str`, Specifies if this training, evaluation or prediction. See `Modes`.
        graph_fn: Graph function. Follows the signature:
            * Args:
                * `mode`: Specifies if this training, evaluation or prediction. See `Modes`.
                * `inputs`: the feature inputs.
        loss_config: An instance of `LossConfig`.
        optimizer_config: An instance of `OptimizerConfig`. Default value `Adam`.
        eval_metrics_config: a list of `MetricConfig` instances.
        discount: `float`. The discount factor on the target Q values.
        exploration_config: An instance `ExplorationConfig`
        use_target_graph: `bool`. To use a second “target” network,
            which we will use to compute target Q values during our updates.
        update_frequency: `int`. At which frequency to update the target graph.
            Only used when `use_target_graph` is set tot True.
        is_continuous: `bool`. Is the model built for a continuous or discrete space.
        dueling: `str` or `bool`. To compute separately the advantage and value functions.
            Options:
                * `True`: creates advantage and state value without any further computation.
                * `mean`, `max`, and `naive`: creates advantage and state value, and computes
                  Q = V(s) + A(s, a)
                  where A = A - mean(A) or A = A - max(A) or A = A.
        use_expert_demo: Whether to pretrain the model on a human/expert data.
        summaries: `str` or `list`. The verbosity of the tensorboard visualization.
            Possible values: `all`, `activations`, `loss`, `learning_rate`, `variables`, `gradients`
        clip_gradients: `float`. Gradients  clipping by global norm.
        clip_embed_gradients: `float`. Embedding gradients clipping to a specified value.
        name: `str`, the name of this model, everything will be encapsulated inside this scope.

     Returns:
        `EstimatorSpec`
    """

    def __init__(self, mode, graph_fn, loss_config, env, state_preprocessing_fn=None,
                 optimizer_config=None, eval_metrics_config=None, discount=0.97,
                 exploration_config=None, use_target_graph=True, update_frequency=5,
                 is_continuous=False, dueling='mean', use_expert_demo=False, summaries='all',
                 clip_gradients=0.5, clip_embed_gradients=0.1, name="Model"):
        self.env = env
        self.num_states = self.env.num_states
        self.num_actions = self.env.num_actions
        self.exploration_config = exploration_config
        self.discount = discount
        self.state_preprocessing_fn = state_preprocessing_fn
        self.use_target_graph = use_target_graph
        self.update_frequency = update_frequency
        self.is_continuous = is_continuous
        self.dueling = dueling
        self.use_expert_demo = use_expert_demo
        super(RLBaseModel, self).__init__(
            mode=mode, name=name, model_type=self.Types.RL, graph_fn=graph_fn,
            loss_config=loss_config, optimizer_config=optimizer_config,
            eval_metrics_config=eval_metrics_config, summaries=summaries,
            clip_gradients=clip_gradients, clip_embed_gradients=clip_embed_gradients)

        self._train_graph = None
        self._target_graph = None

    def _build_exploration(self):
        """Creates the exploration op.

        TODO: Think about whether we should pass the episode number here or internally by
        changing the optimize_loss function????
        """
        return getters.get_exploration(self.exploration_config.module,
                                       **self.exploration_config.params)

    def _build_actions(self):
        """Create the chosen action with an exploration policy."""
        if not self.is_continuous:
            self._index_action = tf.argmax(self._train_results['q'], axis=1)

        # TODO: Add possibility to deactivate the exploration in inference mode.
        batch_size = get_tensor_batch_size(self._train_results['q'])
        exploration_size = tf.concat(axis=0, values=[batch_size, ])

        exploration = self._build_exploration()
        should_explore = tf.random_uniform((), 0, 1) < exploration

        if self.is_continuous:
            pass
        else:
            random_actions = tf.random_uniform(exploration_size, 0, self.num_actions, tf.int64)
            return tf.cond(should_explore, lambda: random_actions, lambda: self._index_action)

    def _build_graph_fn(self):
        """Create the new graph_fn based on the one specified by the user.

        The structure of the graph is the following:
            1 - call the graph specified by the user.
            2 - create the advantage action probabilities, and the state value.
            3 - return the the probabilities, if a dueling method is specified,
                calculate the new probabilities.
        Returns:
            `function`. The graph function.
        """
        def graph_fn(mode, inputs):
            graph_results = self._graph_fn(mode=mode, inputs=inputs)
            a = FullyConnected(mode, num_units=self.num_actions)(graph_results)
            v = None
            q = a
            if self.dueling is not None:
                # Q = V(s) + A(s, a)
                v = FullyConnected(mode, num_units=1)(graph_results)
                if self.dueling == 'mean':
                    q = v + (self.a - tf.reduce_mean(a, axis=1, keep_dims=True))
                elif self.dueling == 'max':
                    q = v + (a - tf.reduce_max(a, axis=1, keep_dims=True))
                elif self.dueling == 'naive':
                    q = v + a
                elif self.dueling is True:
                    q = a

            return {'graph_results': graph_results, 'a': a, 'v': v, 'q': q}

        return graph_fn

    def _call_graph_fn(self, inputs):
        """Calls graph function.

        Creates first one or two graph, i.e. train and target graphs.
        Return the optimal action given an exploration policy.

        If `is_dueling` is set to `True`,
        then another layer is added that represents the state value.

        Args:
            inputs: `Tensor` or `dict` of tensors
        """
        graph_fn = self._build_graph_fn()

        if self.use_target_graph:
            # We create 2 graphs: a training graph and a target graph,
            # so that we can copy one graph to another given a frequency.
            self._train_graph = FunctionModule(
                mode=self.mode, build_fn=graph_fn, name='train')
            self._train_results = self._train_graph(inputs=inputs)
            self._target_graph = FunctionModule(
                mode=self.mode, build_fn=graph_fn, name='target')
            self._target_results = self._target_graph(inputs=inputs)
            return self._build_actions()
        else:
            self._train_results = graph_fn(mode=self.mode, inputs=inputs)
            self._target_results = self._train_results
            return self._build_actions()

    def _build_update_target_graph(self):
        """Creates a copy operation from train graph to target graph."""
        if self.use_target_graph:
            return self._train_graph.copy_from(self._train_graph)
        else:
            return None

    def _build_train_op(self, loss):
        """Creates the training operation,

        In case of use_target_network == True, we append also the update op
        while taking into account the update_frequency.
        """
        # TODO: override optimize loss to include episodes and timesteps numbers
        train_op = super(RLBaseModel, self)._build_train_op(loss)

        # check if we need to update the target graph
        if self.use_target_graph:
            update_op = tf.cond(
                tf.equal(tf.mod(training.get_global_step(), self.update_frequency), 0),
                self._build_update_target_graph,
                lambda: tf.no_op(name='no_op_copy_target'))
            # append the target update op to the train op.
            train_op = tf.group(*[train_op, update_op], name='train_and_update_target')

        return train_op

    def _preprocess(self, features, labels):
        """Model specific preprocessing.

        Args:
            features: `array`, `Tensor` or `dict`. The environment states.
                if `dict` it must contain a `state` key.
            labels: `dict`. A dictionary containing `action`, `reward`, `advantage`.
        """
        if isinstance(features, Mapping) and 'state' not in features:
            raise KeyError("features must include a `state` key.")

        if 'action' not in labels or 'reward' not in labels or 'done' not in labels:
            raise KeyError("labels must include these keys: `action`, `reward`, `done`.")
        return features, labels
