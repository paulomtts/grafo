# Event Callbacks

Hook into node lifecycle events for monitoring, logging, and custom behaviors. Grafo provides callbacks at key lifecycle points:

- `on_connect` - When a node connects to a child
- `on_disconnect` - When a node disconnects from a child
- `on_before_run` - Before node execution
- `on_after_run` - After node execution
- `on_before_forward` - Before forwarding data (during `connect()`)

Callbacks are tuples of `(async_function, kwargs_dict)`. The kwargs dict can contain lambdas for dynamic evaluation.

## Basic Usage

```python
async def log_start(node: Node):
    print(f"Starting {node.uuid}")

async def log_complete(node: Node):
    print(f"Completed {node.uuid} in {node.metadata.runtime}s")

node = Node(coroutine=my_task, uuid="task")
node.on_before_run = (
    log_start,
    dict(node=node)
)
node.on_after_run = (
    log_complete,
    dict(node=node)
)
```

## Modifying Tree Structure Dynamically

A node's coroutine can dynamically connect and disconnect other nodes during execution. This enables adaptive tree structures that change based on runtime conditions.

```python
async def process_success(data: str):
    return f"Success: {data}"

async def process_failure(error: str):
    return f"Failure: {error}"

async def router_coroutine(data: str):
    condition = len(data) > 5
    return condition

async def redirect_callback(
    router_node: Node,
    success_node: Node,
    failure_node: Node
):
    condition = router_node.output
    if condition:
        await router_node.redirect([success_node])
    else:
        await router_node.redirect([failure_node])

success_node = Node(coroutine=process_success, uuid="success")
failure_node = Node(coroutine=process_failure, uuid="failure")

router = Node(
    coroutine=router_coroutine,
    uuid="router",
    kwargs=dict(data="input"),
)

router.on_after_run=(redirect_callback, dict(
    router_node=lambda: router,
    success_node=success_node,
    failure_node=failure_node
))

await router.connect(success_node, forward=Node.AUTO)
await router.connect(failure_node, forward=Node.AUTO)
```

## Next Steps

- [Error Handling](error-handling.md) - Robust error management
- [API Reference](../api-reference/node.md) - Complete callback documentation
