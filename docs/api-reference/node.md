# Node API Reference

Complete API documentation for the `Node` class.

## Class Definition

```python
class Node(Generic[N]):
    """
    A node in an async execution tree.

    Type Parameters:
        N: The expected return type of the coroutine
    """
```

## Constructor

```python
Node(
    coroutine: AwaitableCallback,
    *,
    uuid: str,
    kwargs: Optional[dict] = None,
    timeout: int = 60,
    on_connect: Optional[Callable] = None,
    on_disconnect: Optional[Callable] = None,
    on_before_run: Optional[Callable] = None,
    on_after_run: Optional[Callable] = None
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `coroutine` | `AwaitableCallback` | Required | The async function to execute |
| `uuid` | `str` | Required | Unique identifier for the node |
| `kwargs` | `Optional[dict]` | `None` | Arguments to pass to the coroutine. Values can be static or lambda functions for dynamic evaluation |
| `timeout` | `int` | `60` | Maximum execution time in seconds |
| `on_connect` | `Optional[Callable]` | `None` | Async callback when connecting to a child |
| `on_disconnect` | `Optional[Callable]` | `None` | Async callback when disconnecting from a child |
| `on_before_run` | `Optional[Callable]` | `None` | Async callback before execution |
| `on_after_run` | `Optional[Callable]` | `None` | Async callback after execution |

### Example

```python
async def my_task(value: int):
    return value * 2

node = Node(
    coroutine=my_task,
    uuid="doubler",
    kwargs=dict(value=5),
    timeout=30,
    on_before_run=lambda n: print(f"Starting {n.uuid}")
)
```

## Properties

### output

```python
@property
def output(self) -> Optional[N]:
    """The return value of the coroutine after execution."""
```

Returns `None` before execution completes.

**Example:**
```python
await node.run()
result = node.output  # Access the result
```

### aggregated_output

```python
@property
def aggregated_output(self) -> list:
    """List of outputs from all child nodes."""
```

**Example:**
```python
parent = Node(coroutine=producer, uuid="parent")
child_a = Node(coroutine=task_a, uuid="a")
child_b = Node(coroutine=task_b, uuid="b")

await parent.connect(child_a)
await parent.connect(child_b)

await executor.run()

# Get all child outputs
children_outputs = parent.aggregated_output  # [output_a, output_b]
```

### metadata

```python
@property
def metadata(self) -> Metadata:
    """Execution metadata (runtime, tree level)."""
```

Returns a `Metadata` dataclass with:
- `runtime`: Execution time in seconds (float)
- `level`: Depth in tree, starting from 0 for roots (int)

**Example:**
```python
await node.run()
print(f"Executed in {node.metadata.runtime}s")
print(f"Tree level: {node.metadata.level}")
```

### parents

```python
@property
def parents(self) -> set[Node]:
    """Set of parent nodes."""
```

### children

```python
@property
def children(self) -> set[Node]:
    """Set of child nodes."""
```

### uuid

```python
@property
def uuid(self) -> str:
    """Unique identifier for the node."""
```

## Methods

### connect

```python
async def connect(
    self,
    target: Node,
    *,
    forward: Optional[Union[str, Node.AUTO]] = None,
    on_before_forward: Optional[
        Union[
            OnForwardCallable,
            tuple[OnForwardCallable, Optional[dict[str, Any]]],
        ]
    ] = None
) -> None:
    """
    Connect this node to a child node.

    Args:
        target: The child node to connect to
        forward: Optional forwarding target. Use a string or `Node.AUTO`.
        on_before_forward: Optional callback (or `(callback, fixed_kwargs)`) to transform the forwarded value.

    Raises:
        ForwardingOverrideError: If forwarding conflicts with existing kwarg
        SafeExecutionError: If node is currently running
    """
```

**Example:**
```python
await parent.connect(child)  # Basic connection

await parent.connect(child, forward="data")  # With forwarding

await parent.connect(child, forward=Node.AUTO)  # AUTO (single-input children)

async def transform(value):
    return value.upper()

await parent.connect(
    child,
    forward="data",
    on_before_forward=transform
)
```

### disconnect

```python
async def disconnect(self, target: Node) -> None:
    """
    Disconnect this node from a child node.

    Args:
        target: The child node to disconnect from

    Raises:
        SafeExecutionError: If node is currently running
    """
```

**Example:**
```python
await parent.disconnect(child)
```

### redirect

```python
async def redirect(self, targets: list[Node]) -> None:
    """
    Disconnect all current children and connect to new targets.

    Args:
        targets: List of new child nodes

    Raises:
        SafeExecutionError: If node is currently running
    """
```

**Example:**
```python
# Current children: [old_a, old_b]
await parent.redirect([new_a, new_b, new_c])
# Current children: [new_a, new_b, new_c]
```

### run

```python
async def run(self) -> N:
    """
    Execute the node's coroutine.

    Returns:
        The coroutine's return value

    Raises:
        asyncio.TimeoutError: If execution exceeds timeout
        NotAsyncCallableError: If coroutine is an async generator
        MismatchChunkType: If return type doesn't match generic parameter
    """
```

**Example:**
```python
node = Node(coroutine=my_task, uuid="task")
result = await node.run()
```

### run_yielding

```python
async def run_yielding(self) -> AsyncGenerator[Chunk[N], None]:
    """
    Execute the node's async generator coroutine, yielding chunks.

    Yields:
        Chunk objects wrapping intermediate results

    Raises:
        asyncio.TimeoutError: If execution exceeds timeout
        NotAsyncCallableError: If coroutine is not an async generator
        MismatchChunkType: If yielded type doesn't match generic parameter
    """
```

**Example:**
```python
async def yielding_task():
    for i in range(5):
        yield i

node = Node(coroutine=yielding_task, uuid="yielder")

async for chunk in node.run_yielding():
    print(f"Got: {chunk.output}")
```

## Type Parameters

### Generic Type Validation

Specify expected return type:

```python
# Node that returns string
string_node = Node[str](coroutine=return_string, uuid="str")

# Node that returns int
int_node = Node[int](coroutine=return_int, uuid="int")

# Node that returns custom type
user_node = Node[User](coroutine=get_user, uuid="user")
```

Without type parameter, no validation occurs:

```python
# No type validation
any_node = Node(coroutine=return_anything, uuid="any")
```

## Event Callbacks

### on_connect

```python
async def on_connect_callback(parent: Node, child: Node) -> None:
    """Called when parent connects to child."""
```

### on_disconnect

```python
async def on_disconnect_callback(parent: Node, child: Node) -> None:
    """Called when parent disconnects from child."""
```

### on_before_run

```python
async def on_before_run_callback(node: Node) -> None:
    """Called before node execution."""
```

### on_after_run

```python
async def on_after_run_callback(node: Node) -> None:
    """Called after node execution. Node.output and Node.metadata are available."""
```

### on_before_forward

```python
async def on_before_forward_callback(
    value: Any,
    **kwargs: Any
) -> Any:
    """
    Called before forwarding value to child.
    Receives the forwarded value (positional) plus any `fixed_kwargs` if provided.
    Alternatively, you can declare the parameter as keyword-only `forward_data`.
    """
```

## Complete Example

```python
import asyncio
from grafo import Node, TreeExecutor

async def extract_data(source: str):
    """Extract data from source."""
    await asyncio.sleep(1)
    return f"data_from_{source}"

async def transform_data(data: str):
    """Transform extracted data."""
    await asyncio.sleep(0.5)
    return data.upper()

async def load_data(data: str):
    """Load transformed data."""
    await asyncio.sleep(0.5)
    print(f"Loaded: {data}")
    return "success"

async def log_before(node: Node):
    print(f"Starting {node.uuid}")

async def log_after(node: Node):
    print(f"Completed {node.uuid} in {node.metadata.runtime}s")

async def main():
    # Create nodes
    extractor = Node[str](
        coroutine=extract_data,
        uuid="extractor",
        kwargs=dict(source="database"),
        timeout=30,
        on_before_run=log_before,
        on_after_run=log_after
    )

    transformer = Node[str](
        coroutine=transform_data,
        uuid="transformer",
        on_before_run=log_before,
        on_after_run=log_after
    )

    loader = Node[str](
        coroutine=load_data,
        uuid="loader",
        on_before_run=log_before,
        on_after_run=log_after
    )

    # Build pipeline
    await extractor.connect(transformer, forward="data")
    await transformer.connect(loader, forward="data")

    # Execute
    executor = TreeExecutor(uuid="ETL Pipeline", roots=[extractor])
    await executor.run()

    # Access results
    print(f"Extractor output: {extractor.output}")
    print(f"Transformer output: {transformer.output}")
    print(f"Loader output: {loader.output}")

asyncio.run(main())
```

## See Also

- [TreeExecutor](executor.md) - Execute node trees
- [Chunk](chunk.md) - Wrapper for yielded values
- [Exceptions](exceptions.md) - Error types
