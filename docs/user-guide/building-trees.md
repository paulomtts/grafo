# Building Trees

Learn how to construct complex tree structures for various use cases.

## Tree Patterns

### Linear Chain

The simplest tree structure - a sequence of dependent tasks:

```python
async def step_1():
    return "data_1"

async def step_2(data: str):
    return f"processed_{data}"

async def step_3(data: str):
    return f"final_{data}"

# Build chain
node_1 = Node(coroutine=step_1, uuid="step_1")
node_2 = Node(coroutine=step_2, uuid="step_2")
node_3 = Node(coroutine=step_3, uuid="step_3")

await node_1.connect(node_2, forward_as="data")
await node_2.connect(node_3, forward_as="data")

# Execution: step_1 → step_2 → step_3
```

### Fan-out (Parallel Branches)

One parent spawns multiple parallel child tasks:

```python
async def fetch_data():
    return {"user_id": 123, "items": [1, 2, 3]}

async def process_user(data: dict):
    return f"User: {data['user_id']}"

async def process_items(data: dict):
    return f"Items: {data['items']}"

async def generate_report(data: dict):
    return f"Report for {data['user_id']}"

# Build fan-out
fetcher = Node(coroutine=fetch_data, uuid="fetcher")
user_processor = Node(coroutine=process_user, uuid="user")
items_processor = Node(coroutine=process_items, uuid="items")
reporter = Node(coroutine=generate_report, uuid="report")

await fetcher.connect(user_processor, forward_as="data")
await fetcher.connect(items_processor, forward_as="data")
await fetcher.connect(reporter, forward_as="data")

# All three children run in parallel after fetcher completes
```

### Fan-in (Merge Results)

Multiple parallel tasks converge into one:

```python
async def fetch_source_a():
    await asyncio.sleep(1)
    return "data_a"

async def fetch_source_b():
    await asyncio.sleep(2)
    return "data_b"

async def fetch_source_c():
    await asyncio.sleep(1.5)
    return "data_c"

async def merge_data(a: str, b: str, c: str):
    return f"Merged: {a}, {b}, {c}"

# Build fan-in
source_a = Node(coroutine=fetch_source_a, uuid="source_a")
source_b = Node(coroutine=fetch_source_b, uuid="source_b")
source_c = Node(coroutine=fetch_source_c, uuid="source_c")
merger = Node(coroutine=merge_data, uuid="merger")

await source_a.connect(merger, forward_as="a")
await source_b.connect(merger, forward_as="b")
await source_c.connect(merger, forward_as="c")

# Sources run in parallel, merger waits for all three
executor = TreeExecutor(roots=[source_a, source_b, source_c])
await executor.run()
```

### Diamond Pattern

Combine fan-out and fan-in:

```python
async def root_task():
    return "initial_data"

async def branch_a(data: str):
    return f"a_{data}"

async def branch_b(data: str):
    return f"b_{data}"

async def merge_task(result_a: str, result_b: str):
    return f"merged: {result_a} + {result_b}"

# Build diamond
root = Node(coroutine=root_task, uuid="root")
node_a = Node(coroutine=branch_a, uuid="branch_a")
node_b = Node(coroutine=branch_b, uuid="branch_b")
merger = Node(coroutine=merge_task, uuid="merger")

await root.connect(node_a, forward_as="data")
await root.connect(node_b, forward_as="data")
await node_a.connect(merger, forward_as="result_a")
await node_b.connect(merger, forward_as="result_b")

# Tree shape:
#     root
#     /  \
#    a    b
#     \  /
#    merger
```

### Multi-Root Trees

Start execution from multiple independent entry points:

```python
async def task_group_a():
    return "group_a_result"

async def task_group_b():
    return "group_b_result"

async def task_group_c():
    return "group_c_result"

root_a = Node(coroutine=task_group_a, uuid="root_a")
root_b = Node(coroutine=task_group_b, uuid="root_b")
root_c = Node(coroutine=task_group_c, uuid="root_c")

# All roots start simultaneously
executor = TreeExecutor(
    uuid="Multi-Root",
    roots=[root_a, root_b, root_c]
)
await executor.run()
```

### Hierarchical Pipeline

Build multi-level processing pipelines:

```python
async def extract():
    return "raw_data"

async def transform(data: str):
    return f"transformed_{data}"

async def validate(data: str):
    return f"validated_{data}"

async def save_to_db(data: str):
    return f"saved_{data}"

async def send_notification(result: str):
    return f"notified_{result}"

# Build hierarchy
extract_node = Node(coroutine=extract, uuid="extract")
transform_node = Node(coroutine=transform, uuid="transform")
validate_node = Node(coroutine=validate, uuid="validate")
save_node = Node(coroutine=save_to_db, uuid="save")
notify_node = Node(coroutine=send_notification, uuid="notify")

await extract_node.connect(transform_node, forward_as="data")
await transform_node.connect(validate_node, forward_as="data")
await validate_node.connect(save_node, forward_as="data")
await save_node.connect(notify_node, forward_as="result")

# Linear 5-level pipeline
```

## Dynamic Tree Modification

### Adding Connections During Runtime

```python
async def dynamic_builder():
    # Create initial tree
    root = Node(coroutine=some_task, uuid="root")

    executor = TreeExecutor(roots=[root])

    # Start execution (in background)
    run_task = asyncio.create_task(executor.run())

    # Wait a bit
    await asyncio.sleep(1)

    # Dynamically add new branch
    new_node = Node(coroutine=another_task, uuid="new")
    await root.connect(new_node)

    await run_task
```

Note: Be careful when modifying trees during execution. Grafo will raise `SafeExecutionError` if you try to modify a node that's currently running.

### Redirecting Connections

Change a node's children dynamically:

```python
# Initial setup
await parent.connect(old_child_a)
await parent.connect(old_child_b)

# Redirect to new children
new_child_a = Node(coroutine=new_task_a, uuid="new_a")
new_child_b = Node(coroutine=new_task_b, uuid="new_b")

await parent.redirect([new_child_a, new_child_b])

# old_child_a and old_child_b are now disconnected
# new_child_a and new_child_b are connected
```

### Conditional Branching

Build trees that adapt based on results:

```python
async def check_condition():
    return True  # or False

async def path_a():
    return "took path A"

async def path_b():
    return "took path B"

async def final_step(result: str):
    return f"completed: {result}"

# Build tree
checker = Node(coroutine=check_condition, uuid="checker")
final = Node(coroutine=final_step, uuid="final")

executor = TreeExecutor(roots=[checker])

# Connect based on condition
await executor.run()  # Run checker first

if checker.output:
    node_a = Node(coroutine=path_a, uuid="path_a")
    await checker.connect(node_a)
    await node_a.connect(final, forward_as="result")
else:
    node_b = Node(coroutine=path_b, uuid="path_b")
    await checker.connect(node_b)
    await node_b.connect(final, forward_as="result")

# Continue execution
await executor.run()
```

## Complex Tree Example

Here's a realistic example of a data processing pipeline:

```python
import asyncio
from grafo import Node, TreeExecutor

# Data extraction tasks
async def extract_from_api():
    await asyncio.sleep(1)
    return {"source": "api", "records": 100}

async def extract_from_db():
    await asyncio.sleep(1.5)
    return {"source": "db", "records": 200}

async def extract_from_files():
    await asyncio.sleep(0.5)
    return {"source": "files", "records": 50}

# Data transformation
async def transform_data(data: dict):
    await asyncio.sleep(0.5)
    return {
        "source": data["source"],
        "records": data["records"],
        "transformed": True
    }

# Data validation
async def validate_data(data: dict):
    await asyncio.sleep(0.3)
    return {**data, "valid": True}

# Aggregation
async def aggregate_results(api_data: dict, db_data: dict, file_data: dict):
    total_records = (
        api_data["records"] +
        db_data["records"] +
        file_data["records"]
    )
    return {
        "total_records": total_records,
        "sources": [api_data["source"], db_data["source"], file_data["source"]]
    }

# Final steps
async def save_results(aggregated: dict):
    await asyncio.sleep(0.5)
    return f"Saved {aggregated['total_records']} records"

async def send_notification(result: str):
    await asyncio.sleep(0.2)
    return f"Notification sent: {result}"

async def main():
    # Create extraction nodes (roots)
    api_extract = Node(coroutine=extract_from_api, uuid="api_extract")
    db_extract = Node(coroutine=extract_from_db, uuid="db_extract")
    file_extract = Node(coroutine=extract_from_files, uuid="file_extract")

    # Create transformation nodes
    api_transform = Node(coroutine=transform_data, uuid="api_transform")
    db_transform = Node(coroutine=transform_data, uuid="db_transform")
    file_transform = Node(coroutine=transform_data, uuid="file_transform")

    # Create validation nodes
    api_validate = Node(coroutine=validate_data, uuid="api_validate")
    db_validate = Node(coroutine=validate_data, uuid="db_validate")
    file_validate = Node(coroutine=validate_data, uuid="file_validate")

    # Create aggregation and final nodes
    aggregator = Node(coroutine=aggregate_results, uuid="aggregator")
    saver = Node(coroutine=save_results, uuid="saver")
    notifier = Node(coroutine=send_notification, uuid="notifier")

    # Build tree structure
    # Extract → Transform → Validate chains
    await api_extract.connect(api_transform, forward_as="data")
    await api_transform.connect(api_validate, forward_as="data")

    await db_extract.connect(db_transform, forward_as="data")
    await db_transform.connect(db_validate, forward_as="data")

    await file_extract.connect(file_transform, forward_as="data")
    await file_transform.connect(file_validate, forward_as="data")

    # Validate → Aggregator (fan-in)
    await api_validate.connect(aggregator, forward_as="api_data")
    await db_validate.connect(aggregator, forward_as="db_data")
    await file_validate.connect(aggregator, forward_as="file_data")

    # Aggregator → Saver → Notifier
    await aggregator.connect(saver, forward_as="aggregated")
    await saver.connect(notifier, forward_as="result")

    # Execute tree
    executor = TreeExecutor(
        uuid="Data Processing Pipeline",
        roots=[api_extract, db_extract, file_extract]
    )

    print("Starting pipeline...")
    await executor.run()

    print(f"\nFinal result: {notifier.output}")
    print(f"Total runtime: {notifier.metadata.runtime}s")

    # Show leaf nodes
    leaves = executor.get_leaves()
    print(f"\nLeaf nodes: {[leaf.uuid for leaf in leaves]}")

asyncio.run(main())
```

This creates a tree structure like:

```
api_extract → api_transform → api_validate ─┐
                                             │
db_extract → db_transform → db_validate ────┼─→ aggregator → saver → notifier
                                             │
file_extract → file_transform → file_validate┘
```

## Best Practices

1. **Keep nodes focused**: Each node should do one thing well
2. **Use meaningful UUIDs**: Makes debugging and monitoring easier
3. **Handle errors at appropriate levels**: Catch exceptions where they make sense
4. **Don't create cycles**: Grafo prevents this, but plan your tree structure carefully
5. **Consider parallelism**: Independent branches will run concurrently
6. **Use forwarding wisely**: Balance between automatic and manual forwarding
7. **Test incrementally**: Build and test small sections before combining

## Next Steps

- [Forwarding Data](forwarding-data.md) - Master state passing between nodes
- [Yielding Results](yielding-results.md) - Stream intermediate results
- [Event Callbacks](event-callbacks.md) - Hook into node lifecycle
- [Examples](../examples/common-patterns.md) - More real-world patterns
