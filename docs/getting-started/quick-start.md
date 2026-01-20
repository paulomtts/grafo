# Quick Start

This guide will walk you through creating your first async tree with Grafo.

## Your First Tree

Let's create a simple tree with two nodes:

```python
import asyncio
from grafo import Node, TreeExecutor

# Define async functions
async def greet():
    await asyncio.sleep(1)
    return "Hello"

async def add_name(greeting: str):
    await asyncio.sleep(1)
    return f"{greeting}, World!"

async def main():
    # Create nodes
    node_a = Node(coroutine=greet, uuid="greet")
    node_b = Node(coroutine=add_name, uuid="add_name")

    # Connect nodes with output forwarding
    await node_a.connect(node_b, forward_as="greeting")

    # Create executor and run
    executor = TreeExecutor(uuid="Greeting Tree", roots=[node_a])
    await executor.run()

    # Access results
    print(node_b.output)  # Output: Hello, World!

asyncio.run(main())
```

## What Just Happened?

1. **Defined coroutines**: `greet()` and `add_name()` are async functions
2. **Created nodes**: Wrapped each coroutine in a `Node` object with a unique UUID
3. **Connected nodes**: Made `node_b` a child of `node_a` using `connect()`
4. **Used forwarding**: The `forward_as="greeting"` parameter passes `node_a`'s output to `node_b`'s `greeting` parameter
5. **Created executor**: `TreeExecutor` orchestrates the execution
6. **Ran the tree**: `await executor.run()` executes all nodes respecting dependencies

## Multiple Branches

Trees can have multiple branches that execute in parallel:

```python
import asyncio
from grafo import Node, TreeExecutor

async def root_task():
    return "data"

async def branch_a(data: str):
    await asyncio.sleep(2)
    return f"Branch A processed: {data}"

async def branch_b(data: str):
    await asyncio.sleep(1)
    return f"Branch B processed: {data}"

async def main():
    root = Node(coroutine=root_task, uuid="root")
    node_a = Node(coroutine=branch_a, uuid="branch_a")
    node_b = Node(coroutine=branch_b, uuid="branch_b")

    # Both branches receive root's output
    await root.connect(node_a, forward_as="data")
    await root.connect(node_b, forward_as="data")

    executor = TreeExecutor(uuid="Parallel Tree", roots=[root])
    await executor.run()

    print(node_a.output)  # Branch A processed: data
    print(node_b.output)  # Branch B processed: data

asyncio.run(main())
```

Both branches start simultaneously after `root` completes, executing in parallel.

## Streaming Results

For long-running tasks, you can stream intermediate results:

```python
import asyncio
from grafo import Node, TreeExecutor, Chunk

async def counting_task():
    for i in range(5):
        await asyncio.sleep(0.5)
        yield f"Count: {i}"
    yield "Done!"

async def main():
    node = Node(coroutine=counting_task, uuid="counter")
    executor = TreeExecutor(uuid="Streaming Tree", roots=[node])

    async for item in executor.yielding():
        if isinstance(item, Chunk):
            print(f"Progress: {item.output}")
        elif isinstance(item, Node):
            print(f"Node {item.uuid} completed!")

asyncio.run(main())
```

Output:
```
Progress: Count: 0
Progress: Count: 1
Progress: Count: 2
Progress: Count: 3
Progress: Count: 4
Progress: Done!
Node counter completed!
```

## Manual State Passing

You can use lambda functions for dynamic evaluation:

```python
import asyncio
from grafo import Node, TreeExecutor

shared_state = {"counter": 0}

async def increment():
    await asyncio.sleep(1)
    shared_state["counter"] += 1
    return shared_state["counter"]

async def print_value(value: int):
    print(f"Current value: {value}")
    return "done"

async def main():
    node_a = Node(coroutine=increment, uuid="incrementer")
    node_b = Node(
        coroutine=print_value,
        uuid="printer",
        kwargs=dict(
            value=lambda: node_a.output  # Evaluated when node_b runs
        )
    )

    await node_a.connect(node_b)

    executor = TreeExecutor(uuid="Lambda Tree", roots=[node_a])
    await executor.run()

asyncio.run(main())
```

## Type Validation

Add type safety with generics:

```python
import asyncio
from grafo import Node, TreeExecutor

async def return_string():
    return "text"

async def return_number():
    return 42

async def main():
    # Specify expected return type
    string_node = Node[str](coroutine=return_string, uuid="string")
    number_node = Node[int](coroutine=return_number, uuid="number")

    executor = TreeExecutor(uuid="Typed Tree", roots=[string_node, number_node])
    await executor.run()

    print(f"String: {string_node.output}")
    print(f"Number: {number_node.output}")

asyncio.run(main())
```

If the coroutine returns the wrong type, Grafo will raise an exception.

## Next Steps

Now that you understand the basics, explore:

- [Core Concepts](core-concepts.md) - Deep dive into nodes, trees, and execution
- [Building Trees](../user-guide/building-trees.md) - Advanced tree structures
- [Forwarding Data](../user-guide/forwarding-data.md) - Master state passing
- [API Reference](../api-reference/node.md) - Complete API documentation
