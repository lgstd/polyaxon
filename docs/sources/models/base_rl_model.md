<span style="float:right;">[[source]](https://github.com/polyaxon/polyaxon/blob/master/polyaxon/models/rl/base.py#L18)</span>
## RLBaseModel

```python
polyaxon.models.rl.base.RLBaseModel(mode, graph_fn, loss_config, env, state_preprocessing_fn=None, optimizer_config=None, eval_metrics_config=None, discount=0.97, exploration_config=None, use_target_graph=True, update_frequency=5, is_continuous=False, dueling='mean', use_expert_demo=False, summaries='all', clip_gradients=0.5, clip_embed_gradients=0.1, name='Model')
```

Base reinforcement learning model class.

- __Args__:
	- __mode__: `str`, Specifies if this training, evaluation or prediction. See `Modes`.
	- __graph_fn__: Graph function. Follows the signature:
		* Args:
		* `mode`: Specifies if this training, evaluation or prediction. See `Modes`.
		* `inputs`: the feature inputs.
	- __loss_config__: An instance of `LossConfig`.
	- __optimizer_config__: An instance of `OptimizerConfig`. Default value `Adam`.
	- __eval_metrics_config__: a list of `MetricConfig` instances.
	- __discount__: `float`. The discount factor on the target Q values.
	- __exploration_config__: An instance `ExplorationConfig`
	- __use_target_graph__: `bool`. To use a second “target” network,
		which we will use to compute target Q values during our updates.
	- __update_frequency__: `int`. At which frequency to update the target graph.
		Only used when `use_target_graph` is set tot True.
	- __is_continuous__: `bool`. Is the model built for a continuous or discrete space.
	- __dueling__: `str` or `bool`. To compute separately the advantage and value functions.
		- __Options__:
		* `True`: creates advantage and state value without any further computation.
		* `mean`, `max`, and `naive`: creates advantage and state value, and computes
		  Q = V(s) + A(s, a)
		  where A = A - mean(A) or A = A - max(A) or A = A.
	- __use_expert_demo__: Whether to pretrain the model on a human/expert data.
	- __summaries__: `str` or `list`. The verbosity of the tensorboard visualization.
		Possible values: `all`, `activations`, `loss`, `learning_rate`, `variables`, `gradients`
	- __clip_gradients__: `float`. Gradients  clipping by global norm.
	- __clip_embed_gradients__: `float`. Embedding gradients clipping to a specified value.
	- __name__: `str`, the name of this model, everything will be encapsulated inside this scope.

 - __Returns__:
	`EstimatorSpec`


----

### _build_exploration


```python
_build_exploration(self)
```


Creates the exploration op.

- __TODO__: Think about whether we should pass the episode number here or internally by
changing the optimize_loss function????


----

### _build_actions


```python
_build_actions(self)
```


Create the chosen action with an exploration policy.

----

### _build_graph_fn


```python
_build_graph_fn(self)
```


Create the new graph_fn based on the one specified by the user.

The structure of the graph is the following:
	1 - call the graph specified by the user.
	2 - create the advantage action probabilities, and the state value.
	3 - return the the probabilities, if a dueling method is specified,
	calculate the new probabilities.
- __Returns__:
	`function`. The graph function.


----

### _call_graph_fn


```python
_call_graph_fn(self, inputs)
```


Calls graph function.

Creates first one or two graph, i.e. train and target graphs.
Return the optimal action given an exploration policy.

If `is_dueling` is set to `True`,
then another layer is added that represents the state value.

- __Args__:
	- __inputs__: `Tensor` or `dict` of tensors


----

### _build_update_target_graph


```python
_build_update_target_graph(self)
```


Creates a copy operation from train graph to target graph.

----

### _build_train_op


```python
_build_train_op(self, loss)
```


Creates the training operation,

In case of use_target_network == True, we append also the update op
while taking into account the update_frequency.


----

### _preprocess


```python
_preprocess(self, features, labels)
```


Model specific preprocessing.

- __Args__:
	- __features__: `array`, `Tensor` or `dict`. The environment states.
	if `dict` it must contain a `state` key.
	- __labels__: `dict`. A dictionary containing `action`, `reward`, `advantage`.
