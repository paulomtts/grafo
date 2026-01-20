# Error Handling

Handle errors gracefully in Grafo trees.

## Basic Exception Handling

Exceptions propagate normally:

```python
async def failing_task():
    raise ValueError("Something went wrong")

node = Node(coroutine=failing_task, uuid="failer")
executor = TreeExecutor(roots=[node])

try:
    await executor.run()
except ValueError as e:
    print(f"Caught: {e}")
```

## Timeout Handling

Set node-level timeouts:

```python
async def slow_task():
    await asyncio.sleep(100)
    return "done"

node = Node(
    coroutine=slow_task,
    uuid="slow",
    timeout=5  # 5 seconds (default: 60)
)

try:
    await TreeExecutor(roots=[node]).run()
except asyncio.TimeoutError:
    print(f"Timed out after 5 seconds")
```

## Executor Error Tracking

Check accumulated errors:

```python
executor = TreeExecutor(roots=[root])

try:
    await executor.run()
except Exception as e:
    logger.error(f"Execution failed: {e}")

if executor.errors:
    for error in executor.errors:
        print(f"Error: {error}")
```

## Safe Execution Guards

Grafo prevents modification of running nodes:

```python
from grafo.errors import SafeExecutionError

node = Node(coroutine=my_task, uuid="task")
run_task = asyncio.create_task(executor.run())

try:
    await node.connect(new_child)  # Modification during execution
except SafeExecutionError as e:
    print(f"Cannot modify running node: {e}")

await run_task
```

## Error Recovery Patterns

### Retry Pattern

```python
async def retry_task(max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await unreliable_operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Fallback Pattern

```python
async def task_with_fallback():
    try:
        return await primary_operation()
    except PrimaryError:
        return await fallback_operation()
```

### Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, threshold: int = 3):
        self.failures = 0
        self.threshold = threshold
        self.is_open = False

    async def call(self, func):
        if self.is_open:
            raise Exception("Circuit breaker open")
        try:
            result = await func()
            self.failures = 0
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.threshold:
                self.is_open = True
            raise

breaker = CircuitBreaker()
node = Node(
    coroutine=lambda: breaker.call(unreliable_operation),
    uuid="protected"
)
```

## Handling Forwarding Errors

Validate before forwarding:

```python
async def validate_forward(parent: Node, child: Node, value: Any, required_keys: list) -> Any:
    if not isinstance(value, dict):
        raise ValueError(f"Invalid data from {parent.uuid}")
    if not all(k in value for k in required_keys):
        raise ValueError(f"Missing required keys: {required_keys}")
    return value

await parent.connect(
    child,
    forward_as="data",
    on_before_forward=(validate_forward, {"required_keys": ["id", "name"]})
)
```

## Error Handling in Yielding

Collect partial results:

```python
results = []
try:
    async for item in executor.yielding():
        if isinstance(item, Chunk):
            results.append(item.output)
except Exception as e:
    print(f"Error: {e}")
    print(f"Collected {len(results)} results before error")
```

## Common Exceptions

### ForwardingOverrideError

```python
from grafo.errors import ForwardingOverrideError

node = Node(coroutine=consumer, kwargs=dict(value="preset"))
try:
    await parent.connect(node, forward_as="value")
except ForwardingOverrideError:
    # Can't override existing kwarg
    pass
```

### MismatchChunkType

```python
from grafo.errors import MismatchChunkType

node = Node[str](coroutine=returns_int, uuid="wrong")
try:
    await TreeExecutor(roots=[node]).run()
except MismatchChunkType as e:
    print(f"Type mismatch: {e}")
```

### NotAsyncCallableError

```python
from grafo.errors import NotAsyncCallableError

node = Node(coroutine=regular_coroutine, uuid="regular")
try:
    await node.run_yielding()  # Wrong method
except NotAsyncCallableError:
    # Use run() instead
    await node.run()
```

## Best Practices

1. **Fail fast for logic errors**: Don't catch programming mistakes
2. **Log with context**: Include node UUIDs and details
3. **Handle expected errors**: Retry transient failures
4. **Clean up resources**: Use try/finally for cleanup
5. **Document exceptions**: Note what can be raised

## Next Steps

- [API Reference](../api-reference/exceptions.md) - All exception types
- [Event Callbacks](event-callbacks.md) - Monitor errors
