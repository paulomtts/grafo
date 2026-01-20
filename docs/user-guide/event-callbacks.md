# Event Callbacks

Learn how to hook into node lifecycle events for monitoring, logging, and custom behaviors.

## Overview

Grafo provides event callbacks at key points in the node lifecycle:

- **on_connect**: When a node is connected to a child
- **on_disconnect**: When a node is disconnected from a child
- **on_before_run**: Before a node's coroutine executes
- **on_after_run**: After a node's coroutine completes
- **on_before_forward**: Before forwarding data to a child

All callbacks are async functions that can perform side effects without affecting the tree execution.

## Callback Signatures

### on_connect

Called when a parent connects to a child:

```python
async def on_connect_callback(parent: Node, child: Node):
    print(f"Connected: {parent.uuid} → {child.uuid}")

node = Node(
    coroutine=my_coroutine,
    uuid="parent",
    on_connect=on_connect_callback
)
```

### on_disconnect

Called when a parent disconnects from a child:

```python
async def on_disconnect_callback(parent: Node, child: Node):
    print(f"Disconnected: {parent.uuid} ╳ {child.uuid}")

node = Node(
    coroutine=my_coroutine,
    uuid="parent",
    on_disconnect=on_disconnect_callback
)
```

### on_before_run

Called before the node's coroutine executes:

```python
async def on_before_run_callback(node: Node):
    print(f"Starting {node.uuid}")

node = Node(
    coroutine=my_coroutine,
    uuid="task",
    on_before_run=on_before_run_callback
)
```

### on_after_run

Called after the node's coroutine completes:

```python
async def on_after_run_callback(node: Node):
    print(f"Completed {node.uuid} in {node.metadata.runtime}s")

node = Node(
    coroutine=my_coroutine,
    uuid="task",
    on_after_run=on_after_run_callback
)
```

### on_before_forward

Called before forwarding data to a child, can transform the value:

```python
async def on_before_forward_callback(parent: Node, child: Node, value: Any) -> Any:
    print(f"Forwarding from {parent.uuid} to {child.uuid}")
    return value  # Can transform value here

await parent.connect(
    child,
    forward_as="param",
    on_before_forward=on_before_forward_callback
)
```

## Common Use Cases

### Logging

Track node execution:

```python
import logging
from datetime import datetime

logger = logging.getLogger("grafo")

async def log_before_run(node: Node):
    logger.info(f"[{datetime.now()}] Starting {node.uuid}")

async def log_after_run(node: Node):
    logger.info(
        f"[{datetime.now()}] Completed {node.uuid} "
        f"in {node.metadata.runtime:.2f}s"
    )

node = Node(
    coroutine=my_task,
    uuid="logged_task",
    on_before_run=log_before_run,
    on_after_run=log_after_run
)
```

### Performance Monitoring

Track execution times:

```python
performance_data = {}

async def monitor_performance(node: Node):
    performance_data[node.uuid] = {
        "runtime": node.metadata.runtime,
        "level": node.metadata.level,
        "output_size": len(str(node.output))
    }

node = Node(
    coroutine=my_task,
    uuid="monitored",
    on_after_run=monitor_performance
)

# After execution
await executor.run()
for uuid, data in performance_data.items():
    print(f"{uuid}: {data['runtime']:.3f}s")
```

### State Tracking

Track node states:

```python
from enum import Enum

class NodeState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"

node_states = {}

async def mark_running(node: Node):
    node_states[node.uuid] = NodeState.RUNNING

async def mark_completed(node: Node):
    node_states[node.uuid] = NodeState.COMPLETED

node = Node(
    coroutine=my_task,
    uuid="tracked",
    on_before_run=mark_running,
    on_after_run=mark_completed
)
```

### Data Validation

Validate outputs:

```python
async def validate_output(node: Node):
    if node.output is None:
        raise ValueError(f"{node.uuid} produced None output")

    if isinstance(node.output, dict):
        required_keys = ["id", "name", "status"]
        missing = [k for k in required_keys if k not in node.output]
        if missing:
            raise ValueError(f"{node.uuid} missing keys: {missing}")

node = Node(
    coroutine=my_task,
    uuid="validated",
    on_after_run=validate_output
)
```

### Notification System

Send notifications on completion:

```python
async def send_notification(node: Node):
    # Simulate sending notification
    await send_email(
        subject=f"Task {node.uuid} completed",
        body=f"Output: {node.output}"
    )

node = Node(
    coroutine=important_task,
    uuid="notifiable",
    on_after_run=send_notification
)
```

## Forwarding Transformations

### Data Transformation

Transform data before forwarding:

```python
async def uppercase_transform(parent: Node, child: Node, value: str) -> str:
    return value.upper()

async def produce():
    return "hello"

async def consume(text: str):
    return text  # Receives "HELLO"

parent = Node(coroutine=produce, uuid="parent")
child = Node(coroutine=consume, uuid="child")

await parent.connect(
    child,
    forward_as="text",
    on_before_forward=uppercase_transform
)
```

### Data Enrichment

Add metadata to forwarded values:

```python
import time

async def enrich_data(parent: Node, child: Node, value: dict) -> dict:
    return {
        **value,
        "forwarded_at": time.time(),
        "from_node": parent.uuid,
        "to_node": child.uuid
    }

await parent.connect(
    child,
    forward_as="data",
    on_before_forward=enrich_data
)
```

### Conditional Forwarding

Modify values based on conditions:

```python
async def conditional_forward(parent: Node, child: Node, value: int) -> int:
    # Ensure non-negative
    return max(0, value)

async def threshold_forward(parent: Node, child: Node, value: float) -> float:
    # Cap at maximum
    MAX_VALUE = 100.0
    return min(value, MAX_VALUE)
```

## Multiple Callbacks

Combine multiple callbacks:

```python
async def log_start(node: Node):
    logger.info(f"Starting {node.uuid}")

async def monitor_start(node: Node):
    start_times[node.uuid] = time.time()

async def log_end(node: Node):
    logger.info(f"Completed {node.uuid}")

async def monitor_end(node: Node):
    duration = time.time() - start_times[node.uuid]
    metrics[node.uuid] = duration

# Node with multiple concerns
node = Node(
    coroutine=my_task,
    uuid="multi_callback",
    on_before_run=lambda n: asyncio.gather(log_start(n), monitor_start(n)),
    on_after_run=lambda n: asyncio.gather(log_end(n), monitor_end(n))
)
```

## Callback Context

Access parent/child information:

```python
async def connection_logger(parent: Node, child: Node):
    parent_children_count = len(parent.children)
    child_parents_count = len(child.parents)

    logger.info(
        f"Connection: {parent.uuid} (has {parent_children_count} children) → "
        f"{child.uuid} (has {child_parents_count} parents)"
    )

node = Node(
    coroutine=my_task,
    uuid="parent",
    on_connect=connection_logger
)
```

## Error Handling in Callbacks

Callbacks should handle their own errors:

```python
async def safe_callback(node: Node):
    try:
        # Attempt some side effect
        await risky_operation(node)
    except Exception as e:
        logger.error(f"Callback error for {node.uuid}: {e}")
        # Don't re-raise - don't disrupt execution

node = Node(
    coroutine=my_task,
    uuid="safe",
    on_after_run=safe_callback
)
```

## Advanced Patterns

### Progress Bar

Track progress across tree execution:

```python
from tqdm import tqdm

class ProgressTracker:
    def __init__(self, total_nodes: int):
        self.pbar = tqdm(total=total_nodes)
        self.completed = 0

    async def update_progress(self, node: Node):
        self.completed += 1
        self.pbar.update(1)
        self.pbar.set_description(f"Completed {node.uuid}")

# Create tracker
tracker = ProgressTracker(total_nodes=10)

# Apply to all nodes
for node in all_nodes:
    node.on_after_run = tracker.update_progress
```

### Dependency Graph Visualization

Build a graph during connection:

```python
graph_data = {"nodes": [], "edges": []}

async def record_connection(parent: Node, child: Node):
    if parent.uuid not in graph_data["nodes"]:
        graph_data["nodes"].append(parent.uuid)
    if child.uuid not in graph_data["nodes"]:
        graph_data["nodes"].append(child.uuid)

    graph_data["edges"].append({
        "from": parent.uuid,
        "to": child.uuid
    })

# Apply to all nodes
for node in all_nodes:
    node.on_connect = record_connection

# After building tree
await build_tree()

# Export graph
import json
with open("graph.json", "w") as f:
    json.dump(graph_data, f)
```

### Caching

Cache node outputs:

```python
cache = {}

async def cache_output(node: Node):
    cache[node.uuid] = node.output

async def cached_task():
    # Check cache before execution
    if "task_uuid" in cache:
        return cache["task_uuid"]

    # Otherwise compute
    result = await expensive_computation()
    return result

node = Node(
    coroutine=cached_task,
    uuid="task_uuid",
    on_after_run=cache_output
)
```

### Audit Trail

Create an audit log:

```python
from datetime import datetime
import json

audit_log = []

async def audit_before(node: Node):
    audit_log.append({
        "event": "start",
        "node": node.uuid,
        "timestamp": datetime.now().isoformat(),
        "parents": [p.uuid for p in node.parents]
    })

async def audit_after(node: Node):
    audit_log.append({
        "event": "complete",
        "node": node.uuid,
        "timestamp": datetime.now().isoformat(),
        "runtime": node.metadata.runtime,
        "output_type": type(node.output).__name__
    })

# Apply to all nodes
for node in all_nodes:
    node.on_before_run = audit_before
    node.on_after_run = audit_after

# Save audit log
with open("audit.json", "w") as f:
    json.dump(audit_log, f, indent=2)
```

## Callback Factory

Create reusable callback generators:

```python
def create_logger_callbacks(logger_name: str):
    logger = logging.getLogger(logger_name)

    async def before(node: Node):
        logger.info(f"Starting {node.uuid}")

    async def after(node: Node):
        logger.info(f"Completed {node.uuid} in {node.metadata.runtime}s")

    return before, after

# Use the factory
before_cb, after_cb = create_logger_callbacks("my_tree")

node = Node(
    coroutine=my_task,
    uuid="task",
    on_before_run=before_cb,
    on_after_run=after_cb
)
```

## Best Practices

1. **Keep callbacks simple**: Don't perform heavy computation
2. **Handle errors gracefully**: Don't let callbacks disrupt execution
3. **Avoid side effects that affect execution**: Callbacks observe, don't control
4. **Use callbacks for cross-cutting concerns**: Logging, monitoring, auditing
5. **Document callback expectations**: Especially for forwarding transformations
6. **Test callbacks independently**: Unit test callback logic
7. **Consider performance**: Callbacks add overhead, keep them fast

## Next Steps

- [Error Handling](error-handling.md) - Robust error management
- [Examples](../examples/common-patterns.md) - Real-world callback patterns
- [API Reference](../api-reference/node.md) - Complete callback documentation
