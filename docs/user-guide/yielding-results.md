# Yielding Results

Stream intermediate results from long-running tasks using async generators.

## Overview

Async generators yield intermediate values wrapped in `Chunk` objects containing:
- `uuid`: Source node UUID
- `output`: The yielded value

## Basic Yielding

```python
from grafo import Node, TreeExecutor, Chunk

async def counting_task():
    for i in range(5):
        yield f"Step {i}"

node = Node(coroutine=counting_task, uuid="counter")
executor = TreeExecutor(roots=[node])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"[{item.uuid}] {item.output}")
    elif isinstance(item, Node):
        print(f"Completed: {item.uuid}")
```

## Yielding vs Regular Execution

### Regular (`run()`)

Waits for all nodes, returns everything at once:

```python
nodes, chunks = await executor.run()
# All chunks returned after completion
```

### Yielding (`yielding()`)

Streams results as they arrive:

```python
async for item in executor.yielding():
    # Process results in real-time
    pass
```

## Multiple Yielding Nodes

Results arrive interleaved from parallel nodes:

```python
async def task_a():
    for i in range(3):
        yield f"A{i}"

async def task_b():
    for i in range(3):
        yield f"B{i}"

node_a = Node(coroutine=task_a, uuid="a")
node_b = Node(coroutine=task_b, uuid="b")

executor = TreeExecutor(roots=[node_a, node_b])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(item.output)  # A0, B0, A1, B1, A2, B2 (interleaved)
```

## Latency Control

Adjust check frequency:

```python
async for item in executor.yielding(latency=0.1):  # Check every 100ms
    pass

# Lower latency = more responsive, higher CPU
# Higher latency = less CPU, slower response
# Default: 0.2 (200ms)
```

## Type Validation

Validate yielded types:

```python
async def yield_strings():
    yield "first"
    yield "second"

node = Node[str](coroutine=yield_strings, uuid="typed")
# Raises MismatchChunkType if any yield is not a string
```

## Error Handling

### Partial Results

Collect results before error:

```python
results = []
try:
    async for item in executor.yielding():
        if isinstance(item, Chunk):
            results.append(item.output)
except Exception as e:
    print(f"Error: {e}")
    print(f"Collected {len(results)} results before error")
```

## Mixing Yielding and Regular Nodes

Trees can contain both types:

```python
async def regular_task():
    return "regular result"

async def yielding_task():
    yield "step 1"
    yield "step 2"

# Both work in same tree
```

## Next Steps

- [Type Validation](type-validation.md) - Validate yielded types
- [Event Callbacks](event-callbacks.md) - Monitor progress
