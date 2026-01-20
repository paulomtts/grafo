# Yielding Results

Learn how to stream intermediate results from long-running tasks using async generators.

## Overview

For tasks that produce incremental results, Grafo supports async generators that yield intermediate values. These values are wrapped in `Chunk` objects that include:

- The output value
- The UUID of the node that produced it

This enables real-time progress monitoring and streaming results.

## Basic Yielding

### Simple Async Generator

```python
import asyncio
from grafo import Node, TreeExecutor, Chunk

async def counting_task():
    for i in range(5):
        await asyncio.sleep(0.5)
        yield f"Count: {i}"
    yield "Complete!"

node = Node(coroutine=counting_task, uuid="counter")
executor = TreeExecutor(uuid="Counter", roots=[node])

# Use yielding() instead of run()
async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"Progress from {item.uuid}: {item.output}")
    elif isinstance(item, Node):
        print(f"Node {item.uuid} completed!")
```

Output:
```
Progress from counter: Count: 0
Progress from counter: Count: 1
Progress from counter: Count: 2
Progress from counter: Count: 3
Progress from counter: Count: 4
Progress from counter: Count: Complete!
Node counter completed!
```

### Chunk Structure

```python
@dataclass(frozen=True)
class Chunk:
    uuid: str     # UUID of the source node
    output: Any   # The yielded value
```

Access chunk data:

```python
async for item in executor.yielding():
    if isinstance(item, Chunk):
        source = item.uuid      # Which node produced this
        value = item.output     # The yielded value
```

## Yielding vs Regular Execution

### Using run()

Regular execution waits for all nodes to complete:

```python
async def long_task():
    for i in range(10):
        await asyncio.sleep(1)
        yield f"Step {i}"
    yield "Done"

node = Node(coroutine=long_task, uuid="task")
executor = TreeExecutor(roots=[node])

# Wait 10+ seconds for completion
nodes, chunks = await executor.run()

# All chunks are returned at once
for chunk in chunks:
    print(chunk.output)
```

### Using yielding()

Streaming execution provides results as they arrive:

```python
async def long_task():
    for i in range(10):
        await asyncio.sleep(1)
        yield f"Step {i}"
    yield "Done"

node = Node(coroutine=long_task, uuid="task")
executor = TreeExecutor(roots=[node])

# Stream results as they're produced
async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"Got: {item.output}")  # Prints every ~1 second
```

## Multiple Yielding Nodes

### Parallel Yielding

Multiple nodes can yield simultaneously:

```python
async def task_a():
    for i in range(3):
        await asyncio.sleep(1)
        yield f"A{i}"

async def task_b():
    for i in range(3):
        await asyncio.sleep(1.5)
        yield f"B{i}"

async def task_c():
    for i in range(3):
        await asyncio.sleep(0.8)
        yield f"C{i}"

node_a = Node(coroutine=task_a, uuid="task_a")
node_b = Node(coroutine=task_b, uuid="task_b")
node_c = Node(coroutine=task_c, uuid="task_c")

executor = TreeExecutor(roots=[node_a, node_b, node_c])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"[{item.uuid}] {item.output}")
```

Results arrive interleaved as tasks progress:
```
[task_c] C0
[task_a] A0
[task_c] C1
[task_b] B0
[task_a] A1
[task_c] C2
[task_b] B1
[task_a] A2
[task_b] B2
Node task_c completed!
Node task_a completed!
Node task_b completed!
```

### Sequential Yielding

Nodes with dependencies yield in sequence:

```python
async def step_1():
    for i in range(3):
        yield f"Step1-{i}"

async def step_2():
    for i in range(3):
        yield f"Step2-{i}"

node_1 = Node(coroutine=step_1, uuid="step1")
node_2 = Node(coroutine=step_2, uuid="step2")

await node_1.connect(node_2)

executor = TreeExecutor(roots=[node_1])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(item.output)
```

Output (sequential):
```
Step1-0
Step1-1
Step1-2
Step2-0
Step2-1
Step2-2
```

## Latency Control

Control how frequently the executor checks for new results:

```python
executor = TreeExecutor(roots=[root])

# Check for results every 100ms (default is 200ms)
async for item in executor.yielding(latency=0.1):
    if isinstance(item, Chunk):
        print(item.output)
```

Lower latency = more responsive but slightly higher CPU usage.

## Processing Yields

### Progress Tracking

```python
import asyncio
from datetime import datetime

async def long_process():
    total_steps = 100
    for i in range(total_steps):
        await asyncio.sleep(0.1)
        progress = (i + 1) / total_steps * 100
        yield {"step": i + 1, "progress": progress}

node = Node(coroutine=long_process, uuid="process")
executor = TreeExecutor(roots=[node])

start_time = datetime.now()

async for item in executor.yielding():
    if isinstance(item, Chunk):
        data = item.output
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Step {data['step']}/100 ({data['progress']:.1f}%) - {elapsed:.1f}s elapsed")
    elif isinstance(item, Node):
        total_time = (datetime.now() - start_time).total_seconds()
        print(f"Completed in {total_time:.1f}s")
```

### Real-time UI Updates

```python
async def data_processor():
    datasets = ["dataset_a", "dataset_b", "dataset_c"]
    for dataset in datasets:
        yield {"status": "processing", "dataset": dataset}
        await asyncio.sleep(2)  # Simulate processing
        yield {"status": "complete", "dataset": dataset}

node = Node(coroutine=data_processor, uuid="processor")
executor = TreeExecutor(roots=[node])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        data = item.output
        if data["status"] == "processing":
            print(f"⏳ Processing {data['dataset']}...")
        elif data["status"] == "complete":
            print(f"✓ Completed {data['dataset']}")
```

### Aggregating Yields

Collect all yields for later processing:

```python
node = Node(coroutine=yielding_task, uuid="task")
executor = TreeExecutor(roots=[node])

all_chunks = []
completed_nodes = []

async for item in executor.yielding():
    if isinstance(item, Chunk):
        all_chunks.append(item)
    elif isinstance(item, Node):
        completed_nodes.append(item)

# Process collected data
for chunk in all_chunks:
    print(f"Chunk from {chunk.uuid}: {chunk.output}")
```

## Mixing Yielding and Regular Nodes

Trees can contain both yielding and regular nodes:

```python
async def regular_task():
    return "regular result"

async def yielding_task():
    for i in range(3):
        yield f"yield {i}"

regular_node = Node(coroutine=regular_task, uuid="regular")
yielding_node = Node(coroutine=yielding_task, uuid="yielding")

await regular_node.connect(yielding_node)

executor = TreeExecutor(roots=[regular_node])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"Chunk: {item.output}")
    elif isinstance(item, Node):
        print(f"Node completed: {item.uuid}")
```

Output:
```
Node completed: regular
Chunk: yield 0
Chunk: yield 1
Chunk: yield 2
Node completed: yielding
```

## Type Validation with Yielding

Type hints work with yielding nodes:

```python
async def typed_yielding_task() -> str:
    for i in range(3):
        yield f"string_{i}"  # All yields must be strings

node = Node[str](coroutine=typed_yielding_task, uuid="typed")

# If any yield is not a string, MismatchChunkType is raised
```

## Error Handling

### Handling Exceptions During Yielding

```python
async def risky_task():
    for i in range(5):
        if i == 3:
            raise ValueError("Error at step 3")
        yield f"Step {i}"

node = Node(coroutine=risky_task, uuid="risky")
executor = TreeExecutor(roots=[node])

try:
    async for item in executor.yielding():
        if isinstance(item, Chunk):
            print(item.output)
except ValueError as e:
    print(f"Caught error: {e}")
```

### Graceful Degradation

Continue processing other nodes when one fails:

```python
async def failing_task():
    yield "Start"
    raise Exception("Failed!")

async def successful_task():
    for i in range(3):
        yield f"Success {i}"

fail_node = Node(coroutine=failing_task, uuid="fail")
success_node = Node(coroutine=successful_task, uuid="success")

executor = TreeExecutor(roots=[fail_node, success_node])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(f"[{item.uuid}] {item.output}")
    elif isinstance(item, Node):
        print(f"✓ {item.uuid} completed")

# Check for errors
if executor.errors:
    print(f"Errors: {executor.errors}")
```

## Common Patterns

### Data Streaming Pipeline

```python
async def data_fetcher():
    for page in range(1, 11):
        yield f"page_{page}_data"

async def data_processor(data: str):
    # Process each page
    yield f"processed_{data}"

async def data_saver(result: str):
    # Save result
    yield f"saved_{result}"

fetcher = Node(coroutine=data_fetcher, uuid="fetcher")
processor = Node(coroutine=data_processor, uuid="processor")
saver = Node(coroutine=data_saver, uuid="saver")

await fetcher.connect(processor, forward_as="data")
await processor.connect(saver, forward_as="result")

executor = TreeExecutor(roots=[fetcher])

# Stream the entire pipeline
async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(item.output)
```

### Progress Dashboard

```python
import asyncio
from collections import defaultdict

async def task_with_progress(task_id: str, steps: int):
    for i in range(steps):
        await asyncio.sleep(0.5)
        yield {"task": task_id, "step": i + 1, "total": steps}

# Create multiple tasks
tasks = [
    Node(coroutine=task_with_progress, uuid=f"task_{i}",
         kwargs=dict(task_id=f"task_{i}", steps=5))
    for i in range(3)
]

executor = TreeExecutor(roots=tasks)

# Track progress for each task
progress = defaultdict(lambda: {"current": 0, "total": 0})

async for item in executor.yielding():
    if isinstance(item, Chunk):
        data = item.output
        progress[data["task"]] = {
            "current": data["step"],
            "total": data["total"]
        }

        # Print dashboard
        print("\n" + "="*50)
        for task_id, prog in progress.items():
            pct = prog["current"] / prog["total"] * 100
            bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
            print(f"{task_id}: [{bar}] {pct:.0f}%")
```

## Best Practices

1. **Yield meaningful progress**: Don't yield too frequently or too rarely
2. **Include context in yields**: Add metadata to help consumers understand the data
3. **Use type hints**: Validate yielded types with generics
4. **Handle errors gracefully**: Catch exceptions to prevent pipeline disruption
5. **Consider latency tradeoffs**: Balance responsiveness vs CPU usage
6. **Log progress**: Use yielding for monitoring and debugging

## Next Steps

- [Type Validation](type-validation.md) - Ensure type safety for yields
- [Event Callbacks](event-callbacks.md) - Hook into node lifecycle
- [Error Handling](error-handling.md) - Robust error management
- [Examples](../examples/use-cases.md) - Real-world streaming patterns
