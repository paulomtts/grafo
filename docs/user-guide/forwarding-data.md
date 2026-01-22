# Forwarding Data

Pass state between nodes using automatic or manual forwarding.

## Automatic Forwarding

Specify parameter mapping when connecting:

```python
async def producer():
    return "data"

async def consumer(input_data: str):
    return f"processed_{input_data}"

node_a = Node(coroutine=producer, uuid="producer")
node_b = Node(coroutine=consumer, uuid="consumer")

# Forward node_a's output to node_b's 'input_data' parameter
await node_a.connect(node_b, forward="input_data")
```

!!! info "AUTO Forwarding"
    If the child's coroutine has exactly one eligible parameter, you can omit the name and use automatic forwarding:

    ```python
    await node_a.connect(node_b, forward=Node.AUTO)
    ```

### Multiple Parents

Each parent forwards to different parameters:

```python
async def get_name():
    return "alice"

async def get_age():
    return 30

async def create_profile(name: str, age: int):
    return {"name": name, "age": age}

name_node = Node(coroutine=get_name, uuid="name")
age_node = Node(coroutine=get_age, uuid="age")
profile_node = Node(coroutine=create_profile, uuid="profile")

await name_node.connect(profile_node, forward="name")
await age_node.connect(profile_node, forward="age")
```

## Manual Forwarding

Use lambdas for dynamic evaluation:

```python
node_b = Node(
    coroutine=consumer,
    uuid="consumer",
    kwargs=dict(
        value=lambda: node_a.output  # Evaluated when node_b runs
    )
)

await node_a.connect(node_b)
```

## Forwarding with Transformations

Use `on_before_forward` callback:

```python
async def transform(value: Any) -> Any:
    return value.upper()

await parent.connect(
    child,
    forward="data",
    on_before_forward=transform
)
```

!!! info "How on_before_forward arguments work"
    If you pass only a callback to `on_before_forward`, the callback will receive just the value being forwarded—nothing else.  
    If you need to provide additional arguments, pass a tuple `(callback, fixed_kwargs)`. In this case, `fixed_kwargs` will be merged in when calling your callback.


## Constraints

```python
child = Node(coroutine=task, kwargs=dict(value="preset"))
await parent.connect(child, forward="preset")  # Error!

# Solution: use different parameter or remove preset
```

!!! warning "No override conflicts"
    You can’t forward into a parameter that’s already present in the child’s `kwargs`.

```python
async def consumer(expected_param: str):
    return expected_param

# Correct
await parent.connect(child, forward="expected_param")

# Wrong - raises ForwardingParameterError at connect-time (unless child accepts **kwargs)
await parent.connect(child, forward="wrong_param")
```

!!! warning "Parameter must exist"
    Forwarding parameter must match the child coroutine signature (unless the child accepts `**kwargs`).

## Next Steps

- [Yielding Results](yielding-results.md) - Stream intermediate results
- [Type Validation](type-validation.md) - Ensure type safety
