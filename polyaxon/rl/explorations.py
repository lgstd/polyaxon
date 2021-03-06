# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from collections import OrderedDict

import tensorflow as tf
from tensorflow.python.training.training_util import get_global_step

from polyaxon.libs.utils import get_arguments, track
from polyaxon.rl import exploration_decay


def constant(value=0.5):
    """Builds a constant exploration.

    Args:
        value: `float`. The exploratoin constant to use.

    Returns:
        `function` the exploration function logic.
    """
    return value


def greedy():
    """Builds a greedy exploration. (never selects random values, i.e. random() < 0 == False).

    Returns:
        `function` the exploration function logic.
    """
    return constant(0)


def random():
    """Builds a random exploration (always selects random values, i.e. random() < 1 == True).

    Returns:
        `function` the exploration function logic.
    """
    return constant(1)


def decay(exploration_rate=0.1, decay_type='polynomial_decay', start_decay_at=0, stop_decay_at=1e9,
          decay_rate=0., staircase=False, decay_steps=10000, min_exploration_rate=0):
    """Builds a decaying exploration.

    Decay epsilon based on number of states and the decay_type.

    Args:
        exploration_rate: `float`. The initial value of the exploration rate.
        decay_type: A decay function name defined in `exploration_decay`
            possible Values: exponential_decay, inverse_time_decay, natural_exp_decay,
                             piecewise_constant, polynomial_decay.
        start_decay_at: `int`. When to start the decay.
        stop_decay_at: `int`. When to stop the decay.
        decay_rate: A Python number.  The decay rate.
        staircase: Whether to apply decay in a discrete staircase,
            as opposed to continuous, fashion.
        decay_steps: How often to apply decay.
        min_exploration_rate: `float`. Don't decay below this number.

    Returns:
        `function` the exploration function logic.
    """
    def decay_fn(timestep):
        """The computed decayed exploration rate.

        Args:
            timestep: the current timestep.
        """
        timestep = tf.to_int32(timestep)
        decay_type_fn = getattr(exploration_decay, decay_type)
        kwargs = dict(
            exploration_rate=exploration_rate,
            timestep=tf.minimum(timestep, tf.to_int32(stop_decay_at)) - tf.to_int32(start_decay_at),
            decay_steps=decay_steps,
            name="decayed_exploration_rate"
        )
        decay_fn_args = get_arguments(decay_type_fn)
        if 'decay_rate' in decay_fn_args:
            kwargs['decay_rate'] = decay_rate
        if 'staircase' in decay_fn_args:
            kwargs['staircase'] = staircase

        decayed_exploration_rate = decay_type_fn(**kwargs)

        final_exploration_rate = tf.train.piecewise_constant(
            x=timestep,
            boundaries=[start_decay_at],
            values=[exploration_rate, decayed_exploration_rate])

        if min_exploration_rate:
            final_exploration_rate = tf.maximum(final_exploration_rate, min_exploration_rate)

        return final_exploration_rate

    learning_rate = decay_fn(get_global_step())
    track(learning_rate, tf.GraphKeys.EXPLORATION_RATE)
    return learning_rate


EXPLORATIONS = OrderedDict([
    ('constant', 'constant'),
    ('greedy', 'greedy'),
    ('random', 'random'),
    ('decay', 'decay')
])
