# Core Concepts

Understanding these core concepts will help you build effective async trees with Grafo.

## Nodes

A **Node** is the fundamental building block in Grafo. It represents a unit of work containing:

- An async coroutine function to execute
- Input parameters (kwargs)
- Connections to parent and child nodes
- Metadata about execution

### Node Lifecycle

1. **Creation**: Node is instantiated with a coroutine
2. **Connection**: Node is linked to parents and/or children
3. **Waiting**: Node waits for all parents to complete
4. **Execution**: Node's coroutine runs
5. **Completion**: Node stores output and notifies children

### Node Properties

```python
node = Node(coroutine=my_coroutine, uuid="my_node")

# After execution
node.output        # The return value of the coroutine
node.metadata      # Runtime and tree level information
node.parents       # Set of parent nodes
node.children      # Set of child nodes
```

## Trees

A **tree** is a directed acyclic graph (DAG) of connected nodes. Trees have:

- One or more **root nodes** (nodes with no parents)
- One or more **leaf nodes** (nodes with no children)
- **Connections** defining dependencies between nodes

### Tree Characteristics

**Acyclic**: No cycles allowed - a node cannot be its own ancestor
```python
# This would create a cycle - NOT ALLOWED
await node_a.connect(node_b)
await node_b.connect(node_a)  # Error!
```

**Directed**: Connections flow from parent to child
```python
await parent.connect(child)  # Data flows parent → child
```

**Multiple roots**: A tree can start from multiple independent nodes
```python
executor = TreeExecutor(roots=[root_a, root_b, root_c])
```

### Tree Shapes

**Linear Chain**:
```python
A → B → C → D
```

**Fan-out** (one parent, multiple children):
```python
    A
   /|\
  B C D
```

**Fan-in** (multiple parents, one child):
```python
  A   B   C
   \  |  /
      D
```

**Complex DAG**:
```python
    A
   / \
  B   C
   \ / \
    D   E
     \ /
      F
```

## Execution

The **TreeExecutor** orchestrates node execution with these rules:

### Execution Rules

1. **Dependency Constraint**: A node only runs after ALL its parents have completed
2. **Parallel Execution**: Nodes without dependencies run concurrently
3. **Dynamic Workers**: Worker pool scales automatically based on queue load
4. **Timeout Management**: Each node has a configurable timeout (default: 60s)

### Execution Flow

```python
executor = TreeExecutor(roots=[root_node])
await executor.run()
```

What happens:

1. All root nodes are queued
2. Workers start executing queued nodes
3. When a node completes, its children check if all parents are done
4. If yes, the child is queued for execution
5. Process repeats until all nodes complete

### Dynamic Worker Scaling

The executor adjusts worker count based on:

- Current queue size
- Number of pending nodes
- Execution progress

This means your tree can scale from 1 worker to many workers as needed, without manual configuration.

## State Passing

State can flow between nodes in two ways:

### 1. Manual Forwarding (Lambda Functions)

Evaluate values at runtime:

```python
async def producer():
    return "data"

async def consumer(value: str):
    print(value)

node_a = Node(coroutine=producer, uuid="producer")
node_b = Node(
    coroutine=consumer,
    uuid="consumer",
    kwargs=dict(
        value=lambda: node_a.output  # Evaluated when node_b runs
    )
)

await node_a.connect(node_b)
```

### 2. Automatic Forwarding

Specify forwarding when connecting:

```python
async def producer():
    return "data"

async def consumer(value: str):
    print(value)

node_a = Node(coroutine=producer, uuid="producer")
node_b = Node(coroutine=consumer, uuid="consumer")

await node_a.connect(node_b, forward_as="value")
```

The `forward_as` parameter maps the parent's output to the child's parameter name.

### Forwarding with Multiple Parents

When a node has multiple parents, specify which parent forwards to which parameter:

```python
async def get_name():
    return "Alice"

async def get_age():
    return 30

async def greet(name: str, age: int):
    return f"{name} is {age} years old"

name_node = Node(coroutine=get_name, uuid="name")
age_node = Node(coroutine=get_age, uuid="age")
greet_node = Node(coroutine=greet, uuid="greet")

await name_node.connect(greet_node, forward_as="name")
await age_node.connect(greet_node, forward_as="age")
```

## Chunks and Yielding

For long-running operations, nodes can yield intermediate results:

### Chunk Objects

A `Chunk` wraps intermediate output with metadata:

```python
@dataclass(frozen=True)
class Chunk:
    uuid: str    # Source node's UUID
    output: Any  # The yielded value
```

### Yielding Execution

```python
async def long_task():
    for i in range(10):
        await asyncio.sleep(1)
        yield f"Progress: {i*10}%"
    yield "Complete!"

node = Node(coroutine=long_task, uuid="task")
executor = TreeExecutor(roots=[node])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"[{item.uuid}] {item.output}")
    elif isinstance(item, Node):
        print(f"Node {item.uuid} finished!")
```

### Regular vs Yielding Execution

**Regular execution** (`executor.run()`):
- Waits for all nodes to complete
- Returns all nodes and chunks at once
- Simpler but no progress updates

**Yielding execution** (`executor.yielding()`):
- Streams results as they become available
- Provides real-time progress
- Use for long-running trees

## Type Validation

Grafo supports Python generics for runtime type checking:

```python
async def return_string():
    return "text"

# Specify expected return type
node = Node[str](coroutine=return_string, uuid="typed")

executor = TreeExecutor(roots=[node])
await executor.run()  # Success

# If the coroutine returned an int instead:
# MismatchChunkType exception would be raised
```

Type validation works for:

- Regular return values
- Yielded values from async generators
- Both simple and complex types

## Metadata

Each executed node has metadata:

```python
node.metadata.runtime  # Execution time in seconds
node.metadata.level    # Tree depth (0 for roots)
```

Tree depth is calculated from the root:
```python
# Tree: A → B → C
root.metadata.level     # 0
middle.metadata.level   # 1
leaf.metadata.level     # 2
```

## Events and Callbacks

Nodes support lifecycle event callbacks:

```python
async def log_connection(parent, child):
    print(f"Connected {parent.uuid} → {child.uuid}")

async def before_run(node):
    print(f"Starting {node.uuid}")

async def after_run(node):
    print(f"Completed {node.uuid} in {node.metadata.runtime}s")

node = Node(
    coroutine=my_coroutine,
    uuid="monitored",
    on_connect=log_connection,
    on_before_run=before_run,
    on_after_run=after_run
)
```

Available callbacks:

- `on_connect`: Called when node is connected to a child
- `on_disconnect`: Called when node is disconnected from a child
- `on_before_run`: Called before node execution starts
- `on_after_run`: Called after node execution completes
- `on_before_forward`: Called before forwarding data to a child

## Next Steps

Now that you understand the core concepts:

- [Basic Usage](../user-guide/basic-usage.md) - Common patterns and examples
- [Building Trees](../user-guide/building-trees.md) - Advanced tree construction
- [Forwarding Data](../user-guide/forwarding-data.md) - Master state passing
- [Event Callbacks](../user-guide/event-callbacks.md) - Hook into node lifecycle
