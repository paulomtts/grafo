# Basic Usage

This guide covers common usage patterns for Grafo.

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
    kwargs=dict(a=5, b=3)
)
```

### Node with Timeout

```python
node = Node(
    coroutine=my_task,
    uuid="task_1",
    timeout=30  # 30 seconds timeout (default is 60)
)
```

## Connecting Nodes

### Basic Connection

```python
await parent.connect(child)
```

This creates a dependency: `child` will only run after `parent` completes.

### Connection with Forwarding

```python
await parent.connect(child, forward_as="input_param")
```

The parent's output is passed to the child's `input_param` parameter.

### Multiple Children

```python
await parent.connect(child_a)
await parent.connect(child_b)
await parent.connect(child_c)
```

All children run in parallel after the parent completes.

### Multiple Parents

```python
await parent_a.connect(child, forward_as="param_a")
await parent_b.connect(child, forward_as="param_b")
```

The child waits for BOTH parents to complete before running.

## Disconnecting Nodes

```python
# Disconnect specific child
await parent.disconnect(child)

# Redirect to new children (disconnects all current children first)
await parent.redirect([new_child_a, new_child_b])
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
    uuid="Multi-Root Tree",
    roots=[root_a, root_b, root_c]
)
await executor.run()
```

All roots start executing simultaneously.

### Accessing Node Outputs

```python
await executor.run()

# Individual node output
result = node.output

# Aggregated outputs from all children
aggregated = node.aggregated_output  # List of child outputs
```

### Getting Leaf Nodes

```python
# Get all leaf nodes (nodes with no children)
leaves = executor.get_leaves()

for leaf in leaves:
    print(f"Leaf {leaf.uuid}: {leaf.output}")
```

## Executor Properties

```python
executor.name           # UUID of the executor
executor.description    # Optional description
executor.roots         # List of root nodes
executor.errors        # List of errors encountered during execution
```

## Error Handling

### Node Timeout

```python
import asyncio

async def slow_task():
    await asyncio.sleep(100)  # Will timeout
    return "done"

node = Node(coroutine=slow_task, uuid="slow", timeout=5)
executor = TreeExecutor(roots=[node])

try:
    await executor.run()
except asyncio.TimeoutError:
    print(f"Node {node.uuid} timed out")
```

### Catching Exceptions

```python
async def failing_task():
    raise ValueError("Something went wrong")

node = Node(coroutine=failing_task, uuid="failer")
executor = TreeExecutor(roots=[node])

try:
    await executor.run()
except ValueError as e:
    print(f"Task failed: {e}")
```

### Checking Executor Errors

```python
await executor.run()

if executor.errors:
    print("Errors occurred:")
    for error in executor.errors:
        print(f"  - {error}")
```

## Working with Metadata

```python
await executor.run()

# Access execution metadata
print(f"Runtime: {node.metadata.runtime}s")
print(f"Tree level: {node.metadata.level}")
```

## Stopping Execution

You can stop a running tree gracefully:

```python
import asyncio

async def run_tree():
    executor = TreeExecutor(roots=[root])
    await executor.run()

async def stop_tree():
    await asyncio.sleep(5)  # Wait 5 seconds
    await executor.stop_tree()  # Stop execution

# Run both tasks
await asyncio.gather(run_tree(), stop_tree())
```

## Complete Example

Here's a complete example combining multiple concepts:

```python
import asyncio
from grafo import Node, TreeExecutor

async def fetch_user_data(user_id: int):
    """Simulate API call"""
    await asyncio.sleep(1)
    return {"id": user_id, "name": f"User{user_id}"}

async def fetch_user_posts(user_data: dict):
    """Simulate API call"""
    await asyncio.sleep(1)
    return [f"Post{i}" for i in range(3)]

async def fetch_user_comments(user_data: dict):
    """Simulate API call"""
    await asyncio.sleep(1)
    return [f"Comment{i}" for i in range(5)]

async def aggregate_results(posts: list, comments: list):
    """Combine results"""
    return {
        "posts": posts,
        "comments": comments,
        "total_items": len(posts) + len(comments)
    }

async def main():
    # Create nodes
    user_node = Node(
        coroutine=fetch_user_data,
        uuid="fetch_user",
        kwargs=dict(user_id=123)
    )

    posts_node = Node(
        coroutine=fetch_user_posts,
        uuid="fetch_posts"
    )

    comments_node = Node(
        coroutine=fetch_user_comments,
        uuid="fetch_comments"
    )

    aggregate_node = Node(
        coroutine=aggregate_results,
        uuid="aggregate"
    )

    # Build tree
    # User data fetched first
    await user_node.connect(posts_node, forward_as="user_data")
    await user_node.connect(comments_node, forward_as="user_data")

    # Both posts and comments feed into aggregation
    await posts_node.connect(aggregate_node, forward_as="posts")
    await comments_node.connect(aggregate_node, forward_as="comments")

    # Execute
    executor = TreeExecutor(uuid="User Data Pipeline", roots=[user_node])
    await executor.run()

    # Display results
    print(f"User: {user_node.output}")
    print(f"Final result: {aggregate_node.output}")
    print(f"Total runtime: {aggregate_node.metadata.runtime}s")

asyncio.run(main())
```

Output:
```
User: {'id': 123, 'name': 'User123'}
Final result: {'posts': ['Post0', 'Post1', 'Post2'], 'comments': ['Comment0', 'Comment1', 'Comment2', 'Comment3', 'Comment4'], 'total_items': 8}
Total runtime: 0.003s
```

## Next Steps

- [Building Trees](building-trees.md) - Advanced tree construction patterns
- [Forwarding Data](forwarding-data.md) - Deep dive into state passing
- [Yielding Results](yielding-results.md) - Stream intermediate results
- [Event Callbacks](event-callbacks.md) - Hook into node lifecycle
