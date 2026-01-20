# Core Concepts

Understanding these fundamental concepts will help you use Grafo effectively.

## Nodes

A **Node** wraps an async coroutine function as a unit of work in your tree. Each node:

- Executes an async function
- Has a unique identifier (UUID)
- Connects to parent and child nodes
- Waits for all parents before executing
- Stores output and execution metadata

**Key principle**: A node only runs after ALL its parents complete.

## Trees

A **tree** is a directed acyclic graph (DAG) of connected nodes where:

- **Root nodes** have no parents (entry points)
- **Leaf nodes** have no children (endpoints)
- **Connections** define execution dependencies

Trees are:
- **Directed**: Data flows parent → child
- **Acyclic**: No circular dependencies allowed
- **Flexible**: Can have multiple roots, any shape

## Execution

The **TreeExecutor** orchestrates execution:

1. Queues all root nodes
2. Executes nodes whose parents are complete
3. Manages worker pool dynamically
4. Continues until all nodes finish

Workers scale automatically based on the queue - no manual configuration needed.

## State Passing

Pass data between nodes using:

- **Automatic forwarding**: Specify parameter mapping with `forward_as`
- **Manual forwarding**: Use lambda functions for dynamic evaluation

Choose automatic for simple pass-through, manual for transformations.

## Yielding

Async generator nodes can yield intermediate results wrapped in **Chunk** objects:

- Stream progress updates in real-time
- Monitor long-running operations
- Access results as they're produced

Use `executor.yielding()` instead of `executor.run()` to receive results progressively.

## Type Validation

Add runtime type checking with Python generics:

```python
node = Node[str](coroutine=returns_string, uuid="typed")
```

Validates both regular returns and yielded values against the specified type.

## Metadata

After execution, each node provides:

- `node.output`: The coroutine's return value
- `node.metadata.runtime`: Execution time in seconds
- `node.metadata.level`: Depth in tree (0 for roots)

## Event Callbacks

Hook into node lifecycle for monitoring and logging:

- `on_connect` / `on_disconnect`: Connection events
- `on_before_run` / `on_after_run`: Execution events
- `on_before_forward`: Data forwarding events

Callbacks are tuples of `(async_function, kwargs_dict)`. The kwargs dict can contain lambdas for dynamic evaluation.

## Next Steps

Now that you understand the concepts, learn how to use them:

- [Basic Usage](../user-guide/basic-usage.md) - Create and connect nodes
- [Building Trees](../user-guide/building-trees.md) - Tree structures and patterns
- [Forwarding Data](../user-guide/forwarding-data.md) - Pass state between nodes
- [Yielding Results](../user-guide/yielding-results.md) - Stream intermediate results
