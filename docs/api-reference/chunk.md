# Chunk API Reference

Complete API documentation for the `Chunk` dataclass.

## Class Definition

```python
@dataclass(frozen=True)
class Chunk(Generic[C]):
    """
    Wrapper for intermediate results from async generator nodes.

    A frozen (immutable) dataclass that wraps yielded values with metadata.

    Type Parameters:
        C: The type of the wrapped output value

    Attributes:
        uuid: UUID of the source node that yielded this chunk
        output: The yielded value
    """
```

## Attributes

### uuid

```python
uuid: str
```

The UUID of the node that produced this chunk.

**Example:**
```python
async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"Chunk from node: {item.uuid}")
```

### output

```python
output: C
```

The yielded value from the node's async generator.

**Example:**
```python
async for item in executor.yielding():
    if isinstance(item, Chunk):
        value = item.output
        print(f"Value: {value}")
```

## Usage

### Creating Chunks

Chunks are created automatically by Grafo when nodes yield values. You typically don't create them manually:

```python
async def yielding_task():
    for i in range(5):
        yield f"item_{i}"  # Automatically wrapped in Chunk

node = Node(coroutine=yielding_task, uuid="producer")
```

### Receiving Chunks

Chunks are received when using `TreeExecutor.yielding()`:

```python
executor = TreeExecutor(roots=[node])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        # item is a Chunk object
        source = item.uuid
        value = item.output
```

## Immutability

!!! note "Immutability"
    `Chunk` is a frozen dataclass and cannot be modified.

```python
async for item in executor.yielding():
    if isinstance(item, Chunk):
        try:
            item.output = "new value" # This will raise an error!
        except AttributeError:
            print("Chunks are immutable")
```

## See Also

- [Node](node.md) - Node API for creating yielding coroutines
- [TreeExecutor](executor.md) - Executor API for receiving chunks
- [Yielding Results](../user-guide/yielding-results.md) - Guide to using chunks
