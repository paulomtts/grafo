# Forwarding Data

Learn how to pass state between nodes using Grafo's forwarding mechanisms.

## Overview

Grafo provides two ways to pass data between nodes:

1. **Automatic Forwarding**: Specify parameter mapping when connecting nodes
2. **Manual Forwarding**: Use lambda functions for dynamic evaluation

## Automatic Forwarding

### Basic Forwarding

The simplest way to pass data:

```python
async def producer():
    return "data"

async def consumer(input_data: str):
    return f"processed_{input_data}"

node_a = Node(coroutine=producer, uuid="producer")
node_b = Node(coroutine=consumer, uuid="consumer")

# Forward node_a's output to node_b's 'input_data' parameter
await node_a.connect(node_b, forward_as="input_data")

executor = TreeExecutor(roots=[node_a])
await executor.run()

print(node_b.output)  # "processed_data"
```

### How It Works

When you use `forward_as="param_name"`:

1. Parent node executes and stores its return value in `parent.output`
2. Child node is about to execute
3. Grafo automatically passes `parent.output` to the child's `param_name` parameter
4. Child executes with the forwarded value

### Multiple Children

Forward the same data to multiple nodes:

```python
async def data_source():
    return {"user_id": 123, "status": "active"}

async def log_data(data: dict):
    print(f"Logging: {data}")
    return "logged"

async def save_data(data: dict):
    print(f"Saving: {data}")
    return "saved"

async def notify_data(data: dict):
    print(f"Notifying: {data}")
    return "notified"

source = Node(coroutine=data_source, uuid="source")
logger = Node(coroutine=log_data, uuid="logger")
saver = Node(coroutine=save_data, uuid="saver")
notifier = Node(coroutine=notify_data, uuid="notifier")

# Same data forwarded to all three
await source.connect(logger, forward_as="data")
await source.connect(saver, forward_as="data")
await source.connect(notifier, forward_as="data")

# All three run in parallel with the same input
```

### Multiple Parents

When a node has multiple parents, each can forward to a different parameter:

```python
async def get_username():
    return "alice"

async def get_user_age():
    return 30

async def create_profile(name: str, age: int):
    return f"Profile: {name}, age {age}"

name_node = Node(coroutine=get_username, uuid="name")
age_node = Node(coroutine=get_user_age, uuid="age")
profile_node = Node(coroutine=create_profile, uuid="profile")

await name_node.connect(profile_node, forward_as="name")
await age_node.connect(profile_node, forward_as="age")

executor = TreeExecutor(roots=[name_node, age_node])
await executor.run()

print(profile_node.output)  # "Profile: alice, age 30"
```

### Forwarding Complex Types

Forwarding works with any Python type:

```python
async def produce_dict():
    return {"key1": "value1", "key2": "value2"}

async def produce_list():
    return [1, 2, 3, 4, 5]

async def produce_object():
    return MyCustomClass()

async def consume_dict(data: dict):
    return data["key1"]

async def consume_list(items: list):
    return sum(items)

async def consume_object(obj: MyCustomClass):
    return obj.method()

# Each parent-child pair forwards the appropriate type
```

## Manual Forwarding

### Lambda Functions

Use lambda functions for dynamic evaluation:

```python
async def producer():
    return "data"

async def consumer(value: str):
    return f"processed_{value}"

node_a = Node(coroutine=producer, uuid="producer")
node_b = Node(
    coroutine=consumer,
    uuid="consumer",
    kwargs=dict(
        value=lambda: node_a.output  # Evaluated when node_b runs
    )
)

await node_a.connect(node_b)  # No forward_as needed

executor = TreeExecutor(roots=[node_a])
await executor.run()
```

### When to Use Manual Forwarding

Use lambda functions when you need:

1. **Transformation**: Modify data before passing it

```python
node_b = Node(
    coroutine=consumer,
    kwargs=dict(
        value=lambda: node_a.output.upper()  # Transform to uppercase
    )
)
```

2. **Partial data extraction**: Pass only part of the parent's output

```python
async def producer():
    return {"name": "Alice", "age": 30, "city": "NYC"}

node_a = Node(coroutine=producer, uuid="producer")
node_b = Node(
    coroutine=consumer,
    kwargs=dict(
        name=lambda: node_a.output["name"]  # Extract just the name
    )
)
```

3. **Multiple parent outputs**: Combine data from multiple parents

```python
node_c = Node(
    coroutine=consumer,
    kwargs=dict(
        combined=lambda: f"{node_a.output} + {node_b.output}"
    )
)
```

4. **Conditional values**: Choose values based on conditions

```python
node_b = Node(
    coroutine=consumer,
    kwargs=dict(
        value=lambda: node_a.output if node_a.output > 0 else "default"
    )
)
```

### Static vs Dynamic Values

You can mix static and dynamic kwargs:

```python
node = Node(
    coroutine=my_coroutine,
    kwargs=dict(
        static_param="constant_value",      # Static
        dynamic_param=lambda: some_node.output,  # Dynamic
        another_static=42                   # Static
    )
)
```

## Forwarding with Transformations

### Using on_before_forward Callback

Transform data before forwarding using callbacks:

```python
async def transform_before_forward(parent, child, value):
    # Modify the value before forwarding
    return value.upper() if isinstance(value, str) else value

async def producer():
    return "hello"

async def consumer(data: str):
    return data  # Will receive "HELLO"

node_a = Node(coroutine=producer, uuid="producer")
node_b = Node(coroutine=consumer, uuid="consumer")

await node_a.connect(
    node_b,
    forward_as="data",
    on_before_forward=transform_before_forward
)
```

### Complex Transformations

```python
async def enrich_data(parent, child, value):
    # Add metadata
    return {
        "original": value,
        "from_node": parent.uuid,
        "to_node": child.uuid,
        "timestamp": time.time()
    }

await parent.connect(
    child,
    forward_as="enriched_data",
    on_before_forward=enrich_data
)
```

## Forwarding Constraints

### No Override Conflicts

Forwarding cannot override existing kwargs:

```python
async def consumer(value: str):
    return value

node = Node(
    coroutine=consumer,
    kwargs=dict(value="preset")  # value already set
)

# This will raise ForwardingOverrideError
await parent.connect(node, forward_as="value")
```

Solution: Use a different parameter name or remove the preset value.

### Parameter Must Exist

The forwarding parameter must match a coroutine parameter:

```python
async def consumer(expected_param: str):
    return expected_param

# This will fail - no parameter named 'wrong_param'
await parent.connect(child, forward_as="wrong_param")

# Correct
await parent.connect(child, forward_as="expected_param")
```

## Aggregating Child Outputs

Access all child outputs from a parent:

```python
async def producer():
    return "data"

async def child_a(data: str):
    return f"a_{data}"

async def child_b(data: str):
    return f"b_{data}"

async def child_c(data: str):
    return f"c_{data}"

parent = Node(coroutine=producer, uuid="parent")
node_a = Node(coroutine=child_a, uuid="a")
node_b = Node(coroutine=child_b, uuid="b")
node_c = Node(coroutine=child_c, uuid="c")

await parent.connect(node_a, forward_as="data")
await parent.connect(node_b, forward_as="data")
await parent.connect(node_c, forward_as="data")

executor = TreeExecutor(roots=[parent])
await executor.run()

# Get all child outputs
outputs = parent.aggregated_output
print(outputs)  # ["a_data", "b_data", "c_data"]
```

## Common Patterns

### Pipeline Pattern

Pass data through a chain of transformations:

```python
async def extract():
    return "raw_data"

async def transform(data: str):
    return data.upper()

async def validate(data: str):
    return len(data) > 0

async def load(data: bool):
    return f"loaded: {data}"

extract_node = Node(coroutine=extract, uuid="extract")
transform_node = Node(coroutine=transform, uuid="transform")
validate_node = Node(coroutine=validate, uuid="validate")
load_node = Node(coroutine=load, uuid="load")

await extract_node.connect(transform_node, forward_as="data")
await transform_node.connect(validate_node, forward_as="data")
await validate_node.connect(load_node, forward_as="data")
```

### Map-Reduce Pattern

Distribute work and aggregate results:

```python
async def split_data():
    return [1, 2, 3, 4, 5]

async def process_chunk(chunk: int):
    return chunk * 2

async def reduce_results(r1: int, r2: int, r3: int, r4: int, r5: int):
    return sum([r1, r2, r3, r4, r5])

splitter = Node(coroutine=split_data, uuid="splitter")
processors = [
    Node(coroutine=process_chunk, uuid=f"proc_{i}")
    for i in range(5)
]
reducer = Node(coroutine=reduce_results, uuid="reducer")

# Connect splitter to all processors (manual forwarding for list indexing)
for i, processor in enumerate(processors):
    processor.kwargs["chunk"] = lambda idx=i: splitter.output[idx]
    await splitter.connect(processor)

# Connect all processors to reducer
for i, processor in enumerate(processors):
    await processor.connect(reducer, forward_as=f"r{i+1}")
```

### Conditional Routing Pattern

Route data based on conditions:

```python
async def classifier(data: dict):
    return data["type"]

async def handle_type_a(data: dict):
    return f"Handled as type A: {data}"

async def handle_type_b(data: dict):
    return f"Handled as type B: {data}"

# Build initial tree
classifier_node = Node(
    coroutine=classifier,
    kwargs=dict(data={"type": "A", "value": 123})
)

executor = TreeExecutor(roots=[classifier_node])
await executor.run()

# Route based on classification
if classifier_node.output == "A":
    handler = Node(coroutine=handle_type_a, uuid="handler_a")
elif classifier_node.output == "B":
    handler = Node(coroutine=handle_type_b, uuid="handler_b")

handler.kwargs["data"] = lambda: classifier_node.kwargs["data"]
await classifier_node.connect(handler)
```

## Best Practices

1. **Prefer automatic forwarding**: Simpler and more explicit
2. **Use lambdas for transformations**: When you need to modify data
3. **Name parameters clearly**: Makes forwarding relationships obvious
4. **Document complex forwarding**: Add comments for intricate data flows
5. **Validate inputs**: Check data types in your coroutines
6. **Use type hints**: Helps catch forwarding errors early

## Next Steps

- [Yielding Results](yielding-results.md) - Stream intermediate results
- [Type Validation](type-validation.md) - Ensure type safety
- [Event Callbacks](event-callbacks.md) - Hook into forwarding events
- [Examples](../examples/common-patterns.md) - Real-world forwarding patterns
