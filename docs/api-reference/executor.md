# TreeExecutor API Reference

Complete API documentation for the `TreeExecutor` class.

## Class Definition

```python
class TreeExecutor(Generic[N]):
    """
    Orchestrates execution of async node trees.

    Manages worker pool, dependency resolution, and result streaming.

    Type Parameters:
        N: The type of nodes in the tree
    """
```

## Constructor

```python
TreeExecutor(
    *,
    uuid: str,
    description: Optional[str] = None,
    roots: Optional[list[Node]] = None
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `uuid` | `str` | Required | Unique identifier for the executor |
| `description` | `Optional[str]` | `None` | Optional description of the tree |
| `roots` | `Optional[list[Node]]` | `None` | List of root nodes to start execution from |

### Example

```python
from grafo import TreeExecutor, Node

root_a = Node(coroutine=task_a, uuid="root_a")
root_b = Node(coroutine=task_b, uuid="root_b")

executor = TreeExecutor(
    uuid="My Tree",
    description="Multi-root data processing tree",
    roots=[root_a, root_b]
)
```

## Properties

### name

```python
@property
def name(self) -> str:
    """The UUID of the executor."""
```

**Example:**
```python
print(f"Executing tree: {executor.name}")
```

### description

```python
@property
def description(self) -> Optional[str]:
    """Optional description of the executor."""
```

### roots

```python
@property
def roots(self) -> list[Node]:
    """List of root nodes."""
```

**Example:**
```python
print(f"Tree has {len(executor.roots)} root nodes")
for root in executor.roots:
    print(f"  - {root.uuid}")
```

### errors

```python
@property
def errors(self) -> list[Exception]:
    """List of errors encountered during execution."""
```

**Example:**
```python
await executor.run()

if executor.errors:
    print("Errors occurred:")
    for error in executor.errors:
        print(f"  - {error}")
```

## Methods

### run

```python
async def run(self) -> tuple[list[Node], list[Chunk]]:
    """
    Execute the entire tree and return all results.

    Waits for all nodes to complete before returning.

    Returns:
        Tuple of (completed_nodes, all_chunks)
        - completed_nodes: List of all executed nodes
        - all_chunks: List of all chunks from yielding nodes

    Raises:
        Exceptions from node execution propagate normally
    """
```

**Example:**
```python
executor = TreeExecutor(uuid="Tree", roots=[root])

# Execute and get results
nodes, chunks = await executor.run()

print(f"Executed {len(nodes)} nodes")
print(f"Collected {len(chunks)} chunks")

# Access individual node outputs
for node in nodes:
    print(f"{node.uuid}: {node.output}")
```

### yielding

```python
async def yielding(
    self,
    latency: float = 0.2
) -> AsyncGenerator[Union[Node, Chunk], None]:
    """
    Execute the tree and stream results as they complete.

    Args:
        latency: Check interval in seconds (default: 0.2)

    Yields:
        Node objects when nodes complete, or Chunk objects for intermediate results

    Raises:
        Exceptions from node execution propagate normally
    """
```

**Example:**
```python
executor = TreeExecutor(uuid="Streaming Tree", roots=[root])

async for item in executor.yielding(latency=0.1):
    if isinstance(item, Chunk):
        print(f"[{item.uuid}] Progress: {item.output}")
    elif isinstance(item, Node):
        print(f"Node {item.uuid} completed: {item.output}")
```

**Latency Parameter:**

- Lower latency = more responsive but higher CPU usage
- Higher latency = less CPU usage but slower response
- Default (0.2s) is a good balance for most use cases

### get_leaves

```python
def get_leaves(self) -> list[Node]:
    """
    Get all leaf nodes (nodes with no children).

    Returns:
        List of leaf nodes in the tree

    Raises:
        ValueError: If roots list is empty
    """
```

**Example:**
```python
executor = TreeExecutor(uuid="Tree", roots=[root])

# Get leaf nodes
leaves = executor.get_leaves()

print(f"Found {len(leaves)} leaf nodes:")
for leaf in leaves:
    print(f"  - {leaf.uuid}")
```

### stop_tree

```python
async def stop_tree(self) -> None:
    """
    Gracefully stop tree execution.

    Signals workers to stop processing new nodes.
    """
```

**Example:**
```python
import asyncio

async def run_with_timeout():
    executor = TreeExecutor(roots=[root])

    # Run for maximum 10 seconds
    try:
        await asyncio.wait_for(executor.run(), timeout=10)
    except asyncio.TimeoutError:
        print("Execution timed out, stopping...")
        await executor.stop_tree()
```

## Execution Behavior

### Worker Management

The executor automatically manages a pool of async workers:

- Workers scale dynamically based on queue size
- No manual configuration needed
- Efficient resource utilization

### Dependency Resolution

Nodes execute according to these rules:

1. Root nodes start immediately
2. A node waits for ALL parent nodes to complete
3. Independent branches execute in concurrently
4. Execution continues until all there are no children left to enqueued

### Example Execution Flow

```python
# Tree structure:
#     A
#    / \
#   B   C
#    \ /
#     D

# Execution order:
# 1. A starts (root)
# 2. A completes
# 3. B and C start in concurrently
# 4. B and C complete
# 5. D starts (waits for both B and C)
# 6. D completes
```

## Return Values

### run() Return Value

```python
results = await executor.run()

# results: List[Node]
# - All executed nodes from the tree
# - Access node.output for results
# - Access node.metadata for execution info
```

### yielding() Yield Values

```python
async for item in executor.yielding():
    if isinstance(item, Chunk):
        # Intermediate result from yielding node
        source_uuid = item.uuid
        value = item.output

    elif isinstance(item, Node):
        # Node completed
        result = item.output
        runtime = item.metadata.runtime
```

## See Also

- [Node](node.md) - Node API documentation
- [Chunk](chunk.md) - Chunk data structure
- [Exceptions](exceptions.md) - Error types
