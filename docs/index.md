# Grafo

**Grafo** is a simple yet powerful Python library for building and executing asynchronous task trees. It enables you to orchestrate complex workflows with automatic concurrency management, state passing, and dynamic tree modification.

## What is Grafo?

Grafo allows you to organize asynchronous tasks (coroutines) into tree structures where nodes represent units of work. The library handles execution orchestration with one key principle:

**A node can only start executing once all its parents have finished running.**

This constraint enables powerful patterns like:

- Pipeline processing with dependencies
- Parallel execution of independent branches
- Hierarchical task decomposition
- Dynamic workflow modification during runtime

## Key Features

### Automatic Worker Management
The library dynamically scales the number of concurrent workers based on queue load. You don't need to manually manage thread pools or worker counts.

### Flexible Tree Structures
Trees can have any shape:

- Single or multiple root nodes
- Linear chains or complex DAGs
- Dynamic modifications during runtime

### State Passing
Pass data between nodes in two ways:

- **Manual forwarding**: Use lambda functions for dynamic evaluation
- **Automatic forwarding**: Specify output forwarding when connecting nodes

### Intermediate Results
Yielding coroutines produce `Chunk` objects that wrap intermediate results, allowing you to stream progress updates.

### Type Safety
Use Python generics to validate node outputs at runtime.

### Event Callbacks
Hook into node lifecycle events for monitoring, logging, or custom behaviors.

## Design Philosophy

Grafo follows three core principles:

1. **Follow established nomenclature**: a Node is a Node - precise terminology
2. **Syntax sugar is sweet in moderation**: minimal magic, explicit API
3. **Give the programmer granular control**: fine-grained customization options

## Quick Example

```python
import asyncio
from grafo import Node, TreeExecutor

async def fetch_data():
    await asyncio.sleep(1)
    return "data"

async def process_data(data: str):
    await asyncio.sleep(1)
    return f"processed_{data}"

async def save_result(result: str):
    await asyncio.sleep(1)
    print(f"Saved: {result}")
    return "done"

async def main():
    # Create nodes
    fetcher = Node(coroutine=fetch_data, uuid="fetcher")
    processor = Node(coroutine=process_data, uuid="processor")
    saver = Node(coroutine=save_result, uuid="saver")

    # Build tree with automatic forwarding
    await fetcher.connect(processor, forward_as="data")
    await processor.connect(saver, forward_as="result")

    # Execute
    executor = TreeExecutor(uuid="Pipeline", roots=[fetcher])
    await executor.run()

asyncio.run(main())
```

## Next Steps

- [Installation Guide](getting-started/installation.md) - Get Grafo installed
- [Quick Start](getting-started/quick-start.md) - Build your first tree
- [Core Concepts](getting-started/core-concepts.md) - Understand the fundamentals
- [User Guide](user-guide/basic-usage.md) - Learn all the features

## License

Grafo is released under the MIT License. See the [LICENSE](https://github.com/HappyLoop/grafo/blob/main/LICENSE.txt) file for details.
