# Event Callbacks

Hook into node lifecycle events for monitoring, logging, and custom behaviors.

## Overview

Grafo provides callbacks at key lifecycle points:

- `on_connect` - When a node connects to a child
- `on_disconnect` - When a node disconnects from a child
- `on_before_run` - Before node execution
- `on_after_run` - After node execution
- `on_before_forward` - Before forwarding data (during `connect()`)

Callbacks are tuples of `(async_function, kwargs_dict)`. The kwargs dict can contain lambdas for dynamic evaluation.

## Basic Usage

### Simple Callbacks

```python
async def log_start(node: Node):
    print(f"Starting {node.uuid}")

async def log_complete(node: Node):
    print(f"Completed {node.uuid} in {node.metadata.runtime}s")

node = Node(
    coroutine=my_task,
    uuid="task",
    on_before_run=(log_start, {}),
    on_after_run=(log_complete, {})
)
```

### Callbacks with Arguments

Pass additional arguments via kwargs dict:

```python
async def log_with_level(node: Node, level: str, prefix: str):
    print(f"[{level}] {prefix}: {node.uuid}")

node = Node(
    coroutine=my_task,
    uuid="task",
    on_before_run=(log_with_level, {"level": "INFO", "prefix": "START"}),
    on_after_run=(log_with_level, {"level": "INFO", "prefix": "DONE"})
)
```

## Callback Signatures

### on_connect / on_disconnect

```python
async def connection_callback(parent: Node, child: Node, **kwargs):
    print(f"{parent.uuid} → {child.uuid}")

node = Node(
    coroutine=my_task,
    uuid="parent",
    on_connect=(connection_callback, {"log_level": "DEBUG"})
)
```

### on_before_run / on_after_run

```python
async def execution_callback(node: Node, **kwargs):
    print(f"Node: {node.uuid}")

node = Node(
    coroutine=my_task,
    uuid="task",
    on_before_run=(execution_callback, {"stage": "pre"}),
    on_after_run=(execution_callback, {"stage": "post"})
)
```

### on_before_forward

Passed during `connect()`, can transform forwarded values:

```python
async def transform_forward(parent: Node, child: Node, value: Any, **kwargs) -> Any:
    multiplier = kwargs.get("multiplier", 1)
    return value * multiplier

await parent.connect(
    child,
    forward_as="data",
    on_before_forward=(transform_forward, {"multiplier": 2})
)
```

## Using Lambdas in Callback Kwargs

The kwargs dict can contain lambdas for dynamic evaluation:

```python
async def log_with_context(node: Node, parent_output: str, custom_msg: str):
    print(f"{custom_msg}: {node.uuid} received {parent_output}")

parent_node = Node(coroutine=parent_task, uuid="parent")
child_node = Node(
    coroutine=child_task,
    uuid="child",
    on_before_run=(log_with_context, {
        "parent_output": lambda: parent_node.output,  # Evaluated at runtime
        "custom_msg": "Processing"
    })
)

await parent_node.connect(child_node)
```

## Error Handling in Callbacks

Callbacks should handle their own errors:

```python
async def safe_callback(node: Node, retry_count: int):
    try:
        await risky_operation(node)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        # Don't re-raise - don't disrupt execution

node = Node(
    coroutine=my_task,
    uuid="task",
    on_after_run=(safe_callback, {"retry_count": 3})
)
```

## Next Steps

- [Error Handling](error-handling.md) - Robust error management
- [API Reference](../api-reference/node.md) - Complete callback documentation
