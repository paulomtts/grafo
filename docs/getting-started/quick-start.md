# Quick Start

This guide will walk you through creating your first async tree with Grafo.

## Your First Tree

Create a simple tree with two nodes using automatic forwarding:

```python
import asyncio
from grafo import Node, TreeExecutor

async def greet():
    return "Hello"

async def add_name(greeting: str):
    return f"{greeting}, World!"

async def main():
    # Create nodes
    node_a = Node(coroutine=greet, uuid="greet")
    node_b = Node(coroutine=add_name, uuid="add_name")

    # Connect with automatic forwarding
    await node_a.connect(node_b, forward_as="greeting")

    # Execute tree
    executor = TreeExecutor(uuid="Greeting Tree", roots=[node_a])
    await executor.run()

    print(node_b.output)  # "Hello, World!"

asyncio.run(main())
```

**Key concepts:**
- `Node` wraps an async function with a unique UUID
- `connect()` creates parent-child relationships
- `forward_as="greeting"` automatically passes node_a's output to node_b's `greeting` parameter
- `TreeExecutor` orchestrates execution, ensuring parents run before children

## Parallel Execution

Multiple branches execute in parallel:

```python
async def root_task():
    return "data"

async def process(data: str, label: str):
    return f"{label}: {data}"

root = Node(coroutine=root_task, uuid="root")
branch_a = Node(coroutine=process, uuid="a", kwargs=dict(label="A"))
branch_b = Node(coroutine=process, uuid="b", kwargs=dict(label="B"))

await root.connect(branch_a, forward_as="data")
await root.connect(branch_b, forward_as="data")

executor = TreeExecutor(roots=[root])
await executor.run()
# Both branches run simultaneously after root completes
```

## Streaming Results

Stream intermediate results from async generators:

```python
from grafo import Chunk

async def counting_task():
    for i in range(3):
        yield f"Step {i}"

node = Node(coroutine=counting_task, uuid="counter")
executor = TreeExecutor(roots=[node])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"Progress: {item.output}")
    elif isinstance(item, Node):
        print(f"Completed: {item.uuid}")
```

## Manual Forwarding

Use lambdas for dynamic evaluation or transformations:

```python
async def producer():
    return "data"

async def consumer(value: str):
    return value.upper()

node_a = Node(coroutine=producer, uuid="producer")
node_b = Node(
    coroutine=consumer,
    uuid="consumer",
    kwargs=dict(value=lambda: node_a.output.upper())  # Transform on access
)

await node_a.connect(node_b)
```

## Type Validation

Validate return types at runtime:

```python
async def return_string():
    return "text"

# Specify expected type - validates at runtime
node = Node[str](coroutine=return_string, uuid="typed")
# Raises MismatchChunkType if return type is wrong
```

## Next Steps

Now that you understand the basics, explore:

- [Core Concepts](core-concepts.md) - Deep dive into nodes, trees, and execution
- [Building Trees](../user-guide/building-trees.md) - Advanced tree structures
- [Forwarding Data](../user-guide/forwarding-data.md) - Master state passing
- [API Reference](../api-reference/node.md) - Complete API documentation
