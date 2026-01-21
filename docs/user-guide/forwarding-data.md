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

### AUTO forwarding

If the child has exactly one eligible parameter (not already set in `kwargs`), you can omit the name:

```python
await node_a.connect(node_b, forward=Node.AUTO)
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

### Transformation

Transform data before passing:

```python
kwargs=dict(
    value=lambda: node_a.output.upper()  # Transform to uppercase
)
```

### Extraction

Extract part of parent's output:

```python
kwargs=dict(
    name=lambda: node_a.output["name"]  # Extract just name field
)
```

### Combination

Combine multiple parent outputs:

```python
kwargs=dict(
    combined=lambda: f"{node_a.output} + {node_b.output}"
)
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

!!! info "Fixed kwargs for callbacks"
    If you need extra fixed kwargs, pass a tuple `(callback, fixed_kwargs)`.

```python
async def scale_value(value: Any, multiplier: int) -> Any:
    return value * multiplier

await parent.connect(
    child,
    forward="data",
    on_before_forward=(scale_value, {"multiplier": lambda: some_node.output})
)
```

## Constraints

!!! warning "No override conflicts"
    You can’t forward into a parameter that’s already present in the child’s `kwargs`.

```python
# This raises ForwardingOverrideError
child = Node(coroutine=task, kwargs=dict(value="preset"))
await parent.connect(child, forward="value")  # Error!

# Solution: use different parameter or remove preset
```

!!! warning "Parameter must exist"
    Forwarding parameter must match the child coroutine signature (unless the child accepts `**kwargs`).

```python
async def consumer(expected_param: str):
    return expected_param

# Correct
await parent.connect(child, forward="expected_param")

# Wrong - raises ForwardingParameterError at connect-time (unless child accepts **kwargs)
await parent.connect(child, forward="wrong_param")
```

## Aggregating Child Outputs

Access all child outputs from parent:

```python
await parent.connect(child_a, forward="data")
await parent.connect(child_b, forward="data")
await parent.connect(child_c, forward="data")

await executor.run()

outputs = parent.aggregated_output  # List of all child outputs
```

## Next Steps

- [Yielding Results](yielding-results.md) - Stream intermediate results
- [Type Validation](type-validation.md) - Ensure type safety
