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
results = await executor.run()
# All chunks returned after completion
```

### Yielding (`yielding()`)

Streams results as they arrive:

```python
async for item in executor.yielding():
    # Process results in real-time
    pass
```

!!! info "Mixing Yielding and Regular Nodes"
    You can build trees where some nodes use `yield` (producing intermediate chunks) while others return a value normally. When you run the tree with `.yielding()`, you’ll receive each yielded result from generator-nodes *as soon as it’s available*, as well as each regular node’s result when it completes.  



## Next Steps

- [Type Validation](type-validation.md) - Validate yielded types
- [Event Callbacks](event-callbacks.md) - Monitor progress
