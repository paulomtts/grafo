# Basic Usage

Common operations with nodes and executors.

## Creating Nodes

### Simple Node

```python
from grafo import Node

async def my_task():
    return "result"

node = Node(coroutine=my_task, uuid="task_1")
```

### Node with Parameters

```python
async def add_numbers(a: int, b: int):
    return a + b

node = Node(
    coroutine=add_numbers,
    uuid="adder",
    kwargs=dict(a=5, b=3),
    timeout=30  # Optional timeout in seconds (default: 60)
)
```

## Connecting Nodes

### Basic Connection

```python
await parent.connect(child)
```

### With Forwarding

```python
await parent.connect(child, forward="input_param")
```

### Multiple Children (Parallel)

```python
await parent.connect(child_a)
await parent.connect(child_b)
await parent.connect(child_c)
# All children run in parallel after parent completes
```

### Multiple Parents (Fan-in)

```python
await parent_a.connect(child, forward="param_a")
await parent_b.connect(child, forward="param_b")
# Child waits for BOTH parents before running
```

## Executing Trees

### Basic Execution

```python
from grafo import TreeExecutor

executor = TreeExecutor(uuid="My Tree", roots=[root_node])
await executor.run()

# Access results
print(root_node.output)
```

### Multiple Roots

```python
executor = TreeExecutor(
    uuid="Multi-Root",
    roots=[root_a, root_b, root_c]
)
await executor.run()
# All roots start simultaneously
```

### Accessing Results

```python
await executor.run()

result = node.output  # Individual node output
runtime = node.metadata.runtime  # Execution time in seconds
level = node.metadata.level  # Tree depth (0 for roots)
```

## Error Handling

```python
try:
    await executor.run()
except asyncio.TimeoutError:
    print(f"Node timed out")
except ValueError as e:
    print(f"Task failed: {e}")

# Check executor errors
if executor.errors:
    for error in executor.errors:
        print(f"Error: {error}")
```

## Disconnecting Nodes

```python
# Disconnect specific child
await parent.disconnect(child)

# Redirect to new children
await parent.redirect([new_child_a, new_child_b])
```

## Next Steps

- [Building Trees](building-trees.md) - Advanced tree structures
- [Forwarding Data](forwarding-data.md) - State passing patterns
