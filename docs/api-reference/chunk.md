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

### Type Checking

Use `isinstance()` to distinguish chunks from nodes:

```python
async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"Chunk: {item.output}")
    elif isinstance(item, Node):
        print(f"Node completed: {item.uuid}")
```

## Type Parameters

### Generic Chunk Types

Chunks preserve type information:

```python
async def yield_strings():
    yield "first"
    yield "second"

async def yield_numbers():
    yield 1
    yield 2

string_node = Node[str](coroutine=yield_strings, uuid="strings")
number_node = Node[int](coroutine=yield_numbers, uuid="numbers")

executor = TreeExecutor(roots=[string_node, number_node])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        # item.output type is preserved
        if item.uuid == "strings":
            # item is Chunk[str]
            text: str = item.output
        elif item.uuid == "numbers":
            # item is Chunk[int]
            number: int = item.output
```

## Immutability

Chunks are frozen dataclasses and cannot be modified:

```python
async for item in executor.yielding():
    if isinstance(item, Chunk):
        # This will raise an error
        try:
            item.output = "new value"
        except AttributeError:
            print("Chunks are immutable")
```

## Comparison and Equality

Chunks can be compared based on their attributes:

```python
chunk1 = Chunk(uuid="node_1", output="value")
chunk2 = Chunk(uuid="node_1", output="value")
chunk3 = Chunk(uuid="node_2", output="value")

assert chunk1 == chunk2  # Same uuid and output
assert chunk1 != chunk3  # Different uuid
```

## Common Patterns

### Collecting Chunks by Source

```python
from collections import defaultdict

chunks_by_node = defaultdict(list)

async for item in executor.yielding():
    if isinstance(item, Chunk):
        chunks_by_node[item.uuid].append(item.output)

# Process chunks by source
for node_uuid, values in chunks_by_node.items():
    print(f"{node_uuid} produced {len(values)} chunks")
```

### Processing Chunks in Real-Time

```python
async for item in executor.yielding():
    if isinstance(item, Chunk):
        # Process immediately
        await process_value(item.output)

        # Log progress
        logger.info(f"Processed chunk from {item.uuid}")

        # Update UI
        ui.update_progress(item.uuid, item.output)
```

### Filtering Chunks

```python
async for item in executor.yielding():
    if isinstance(item, Chunk):
        # Only process chunks from specific nodes
        if item.uuid in ["important_node_1", "important_node_2"]:
            await handle_important_chunk(item.output)

        # Only process chunks with specific values
        if item.output.startswith("ERROR"):
            await handle_error(item.output)
```

### Aggregating Chunks

```python
all_chunks = []

async for item in executor.yielding():
    if isinstance(item, Chunk):
        all_chunks.append(item)

# Aggregate by node
from itertools import groupby

all_chunks.sort(key=lambda c: c.uuid)
for node_uuid, chunks in groupby(all_chunks, key=lambda c: c.uuid):
    outputs = [c.output for c in chunks]
    print(f"{node_uuid}: {len(outputs)} chunks")
```

### Progress Tracking

```python
from datetime import datetime

progress = {}

async for item in executor.yielding():
    if isinstance(item, Chunk):
        if item.uuid not in progress:
            progress[item.uuid] = {
                "start": datetime.now(),
                "chunks": 0
            }

        progress[item.uuid]["chunks"] += 1
        progress[item.uuid]["last_update"] = datetime.now()

        # Display progress
        p = progress[item.uuid]
        elapsed = (p["last_update"] - p["start"]).total_seconds()
        print(f"{item.uuid}: {p['chunks']} chunks in {elapsed:.1f}s")
```

## Complete Example

```python
import asyncio
from grafo import Node, TreeExecutor, Chunk

async def download_file(url: str, filename: str):
    """Simulate file download with progress updates."""
    total_chunks = 10
    for i in range(total_chunks):
        await asyncio.sleep(0.5)
        progress = (i + 1) / total_chunks * 100
        yield {
            "filename": filename,
            "chunk": i + 1,
            "total": total_chunks,
            "progress": progress
        }

async def main():
    # Create download tasks
    downloads = [
        Node[dict](
            coroutine=download_file,
            uuid=f"download_{i}",
            kwargs=dict(
                url=f"https://example.com/file{i}.zip",
                filename=f"file{i}.zip"
            )
        )
        for i in range(3)
    ]

    executor = TreeExecutor(uuid="Downloads", roots=downloads)

    # Track progress for each download
    progress_bars = {}

    async for item in executor.yielding():
        if isinstance(item, Chunk):
            data = item.output
            filename = data["filename"]

            # Update progress
            progress_bars[filename] = data["progress"]

            # Display
            bar = "█" * int(data["progress"] // 5) + "░" * (20 - int(data["progress"] // 5))
            print(f"{filename}: [{bar}] {data['progress']:.0f}% ({data['chunk']}/{data['total']})")

        elif isinstance(item, Node):
            print(f"✓ {item.uuid} completed")

    print(f"\nAll downloads complete!")

asyncio.run(main())
```

Output:
```
file0.zip: [██░░░░░░░░░░░░░░░░░░] 10% (1/10)
file1.zip: [██░░░░░░░░░░░░░░░░░░] 10% (1/10)
file2.zip: [██░░░░░░░░░░░░░░░░░░] 10% (1/10)
file0.zip: [████░░░░░░░░░░░░░░░░] 20% (2/10)
...
file0.zip: [████████████████████] 100% (10/10)
✓ download_0 completed
file1.zip: [████████████████████] 100% (10/10)
✓ download_1 completed
file2.zip: [████████████████████] 100% (10/10)
✓ download_2 completed

All downloads complete!
```

## Type Validation

Chunks respect type validation from their source nodes:

```python
async def typed_yielder():
    yield "string1"
    yield "string2"
    yield 123  # Wrong type!

node = Node[str](coroutine=typed_yielder, uuid="typed")

try:
    async for item in TreeExecutor(roots=[node]).yielding():
        if isinstance(item, Chunk):
            print(item.output)
except Exception as e:
    print(f"Type error: {e}")
    # MismatchChunkType raised on third yield
```

## See Also

- [Node](node.md) - Node API for creating yielding coroutines
- [TreeExecutor](executor.md) - Executor API for receiving chunks
- [Yielding Results](../user-guide/yielding-results.md) - Guide to using chunks
