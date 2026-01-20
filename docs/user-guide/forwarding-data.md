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
await node_a.connect(node_b, forward_as="input_data")
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

await name_node.connect(profile_node, forward_as="name")
await age_node.connect(profile_node, forward_as="age")
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
async def transform(parent: Node, child: Node, value: Any, **kwargs) -> Any:
    return value.upper()

await parent.connect(
    child,
    forward_as="data",
    on_before_forward=(transform, {})
)
```

The kwargs dict can contain lambdas:

```python
async def scale_value(parent: Node, child: Node, value: Any, multiplier: int) -> Any:
    return value * multiplier

await parent.connect(
    child,
    forward_as="data",
    on_before_forward=(scale_value, {"multiplier": lambda: some_node.output})
)
```

## Constraints

### No Override Conflicts

Can't forward to pre-set parameters:

```python
# This raises ForwardingOverrideError
child = Node(coroutine=task, kwargs=dict(value="preset"))
await parent.connect(child, forward_as="value")  # Error!

# Solution: use different parameter or remove preset
```

### Parameter Must Exist

Forwarding parameter must match coroutine signature:

```python
async def consumer(expected_param: str):
    return expected_param

# Correct
await parent.connect(child, forward_as="expected_param")

# Wrong - raises error
await parent.connect(child, forward_as="wrong_param")
```

## Aggregating Child Outputs

Access all child outputs from parent:

```python
await parent.connect(child_a, forward_as="data")
await parent.connect(child_b, forward_as="data")
await parent.connect(child_c, forward_as="data")

await executor.run()

outputs = parent.aggregated_output  # List of all child outputs
```

## Next Steps

- [Yielding Results](yielding-results.md) - Stream intermediate results
- [Type Validation](type-validation.md) - Ensure type safety
