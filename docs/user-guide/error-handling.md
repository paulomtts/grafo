# Error Handling

Learn how to handle errors gracefully in Grafo trees.

## Overview

Grafo provides several mechanisms for error handling:

- Exception propagation from nodes
- Timeout handling
- Safe execution guards
- Executor error tracking
- Custom error recovery

## Basic Exception Handling

### Catching Node Exceptions

Exceptions in node coroutines propagate normally:

```python
import asyncio
from grafo import Node, TreeExecutor

async def failing_task():
    raise ValueError("Something went wrong!")

node = Node(coroutine=failing_task, uuid="failer")
executor = TreeExecutor(roots=[node])

try:
    await executor.run()
except ValueError as e:
    print(f"Caught error: {e}")
```

### Handling Errors in Coroutines

Handle errors within your coroutine:

```python
async def safe_task():
    try:
        result = await risky_operation()
        return result
    except SomeException as e:
        logger.error(f"Operation failed: {e}")
        return default_value  # Fallback

node = Node(coroutine=safe_task, uuid="safe")
```

## Timeout Handling

### Node-Level Timeouts

Each node has a configurable timeout:

```python
import asyncio

async def slow_task():
    await asyncio.sleep(100)  # Takes too long
    return "done"

node = Node(
    coroutine=slow_task,
    uuid="slow",
    timeout=5  # 5 second timeout (default is 60)
)

executor = TreeExecutor(roots=[node])

try:
    await executor.run()
except asyncio.TimeoutError:
    print(f"Node {node.uuid} timed out after 5 seconds")
```

### Handling Timeouts Gracefully

```python
async def task_with_timeout():
    try:
        result = await asyncio.wait_for(long_operation(), timeout=5)
        return result
    except asyncio.TimeoutError:
        logger.warning("Operation timed out, using cached result")
        return get_cached_result()

node = Node(coroutine=task_with_timeout, uuid="resilient")
```

## Executor Error Tracking

### Checking for Errors

The executor tracks errors that occur:

```python
executor = TreeExecutor(roots=[root_node])

try:
    await executor.run()
except Exception as e:
    logger.error(f"Execution failed: {e}")

# Check accumulated errors
if executor.errors:
    print(f"Encountered {len(executor.errors)} errors:")
    for error in executor.errors:
        print(f"  - {error}")
```

### Multiple Node Errors

When multiple nodes fail:

```python
async def task_a():
    raise ValueError("Error A")

async def task_b():
    raise TypeError("Error B")

async def task_c():
    return "success"

node_a = Node(coroutine=task_a, uuid="a")
node_b = Node(coroutine=task_b, uuid="b")
node_c = Node(coroutine=task_c, uuid="c")

executor = TreeExecutor(roots=[node_a, node_b, node_c])

try:
    await executor.run()
except Exception:
    # Check which nodes failed
    for error in executor.errors:
        print(f"Error: {error}")
```

## Safe Execution Guards

### SafeExecutionError

Grafo prevents modification of running nodes:

```python
from grafo.errors import SafeExecutionError

async def modify_during_run():
    node = Node(coroutine=some_task, uuid="task")
    executor = TreeExecutor(roots=[node])

    # Start execution
    run_task = asyncio.create_task(executor.run())

    # Try to modify while running
    try:
        new_child = Node(coroutine=other_task, uuid="new")
        await node.connect(new_child)  # Will raise SafeExecutionError
    except SafeExecutionError as e:
        print(f"Cannot modify running node: {e}")

    await run_task
```

## Custom Error Handling

### Error Recovery Patterns

#### Retry Pattern

```python
async def retry_task(max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            result = await unreliable_operation()
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Give up
            logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

node = Node(coroutine=retry_task, uuid="retry")
```

#### Fallback Pattern

```python
async def task_with_fallback():
    try:
        return await primary_operation()
    except PrimaryError:
        logger.warning("Primary failed, trying fallback")
        try:
            return await fallback_operation()
        except FallbackError:
            logger.error("Both primary and fallback failed")
            return default_value

node = Node(coroutine=task_with_fallback, uuid="fallback")
```

#### Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.is_open = False

    async def call(self, func):
        if self.is_open:
            raise Exception("Circuit breaker is open")

        try:
            result = await func()
            self.failure_count = 0  # Reset on success
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.error("Circuit breaker opened")
            raise

breaker = CircuitBreaker()

async def protected_task():
    return await breaker.call(unreliable_operation)

node = Node(coroutine=protected_task, uuid="protected")
```

## Error Handling with Forwarding

### Validating Forwarded Data

```python
async def validate_input(data: dict):
    required_keys = ["id", "name", "status"]
    missing = [k for k in required_keys if k not in data]

    if missing:
        raise ValueError(f"Missing required keys: {missing}")

    return process_data(data)

async def on_before_forward_validate(parent: Node, child: Node, value: dict) -> dict:
    # Validate before forwarding
    required_keys = ["id", "name"]
    if not all(k in value for k in required_keys):
        raise ValueError(f"Invalid data from {parent.uuid}")
    return value

await parent.connect(
    child,
    forward_as="data",
    on_before_forward=on_before_forward_validate
)
```

### Handling Forward Errors

```python
async def safe_forward(parent: Node, child: Node, value: Any) -> Any:
    try:
        # Attempt transformation
        return transform(value)
    except Exception as e:
        logger.error(f"Forward transformation failed: {e}")
        # Return original value as fallback
        return value

await parent.connect(
    child,
    forward_as="data",
    on_before_forward=safe_forward
)
```

## Error Handling in Yielding Execution

### Partial Results on Error

```python
async def partial_yielding_task():
    for i in range(10):
        if i == 5:
            raise ValueError("Error at step 5")
        yield f"Step {i}"

node = Node(coroutine=partial_yielding_task, uuid="partial")
executor = TreeExecutor(roots=[node])

results = []
try:
    async for item in executor.yielding():
        if isinstance(item, Chunk):
            results.append(item.output)
except ValueError as e:
    print(f"Error occurred: {e}")
    print(f"Collected {len(results)} results before error")
```

### Continue on Error

Process other nodes even when one fails:

```python
async def task_a():
    for i in range(3):
        yield f"A{i}"

async def task_b():
    yield "B0"
    raise ValueError("B failed")

async def task_c():
    for i in range(3):
        yield f"C{i}"

node_a = Node(coroutine=task_a, uuid="a")
node_b = Node(coroutine=task_b, uuid="b")
node_c = Node(coroutine=task_c, uuid="c")

executor = TreeExecutor(roots=[node_a, node_b, node_c])

errors = []
results = []

async for item in executor.yielding():
    try:
        if isinstance(item, Chunk):
            results.append(item.output)
    except Exception as e:
        errors.append(e)
        continue  # Keep processing other nodes

print(f"Results: {results}")
print(f"Errors: {errors}")
```

## Error Handling Best Practices

### 1. Fail Fast vs Fail Safe

**Fail Fast** - Let errors propagate:

```python
async def fail_fast_task():
    data = await fetch_data()
    # No error handling - let it fail
    return process(data)
```

**Fail Safe** - Handle and recover:

```python
async def fail_safe_task():
    try:
        data = await fetch_data()
        return process(data)
    except Exception as e:
        logger.error(f"Error: {e}")
        return get_default_data()
```

### 2. Log Errors Appropriately

```python
import logging

logger = logging.getLogger(__name__)

async def well_logged_task():
    try:
        result = await operation()
        return result
    except ValueError as e:
        logger.warning(f"Expected error: {e}")
        return default_value
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
```

### 3. Clean Up Resources

```python
async def resource_safe_task():
    resource = None
    try:
        resource = await acquire_resource()
        result = await use_resource(resource)
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise
    finally:
        if resource:
            await release_resource(resource)
```

### 4. Use Custom Exceptions

```python
class DataProcessingError(Exception):
    pass

class ValidationError(Exception):
    pass

async def typed_error_task():
    try:
        data = await fetch_data()
    except NetworkError as e:
        raise DataProcessingError(f"Failed to fetch: {e}")

    if not validate(data):
        raise ValidationError("Data validation failed")

    return process(data)
```

## Error Recovery Strategies

### Strategy 1: Default Values

```python
async def with_defaults():
    try:
        return await fetch_from_api()
    except Exception:
        return {"status": "unavailable", "data": []}
```

### Strategy 2: Cached Results

```python
cache = {}

async def with_cache():
    try:
        result = await fetch_from_api()
        cache["last_result"] = result
        return result
    except Exception:
        if "last_result" in cache:
            logger.warning("Using cached result")
            return cache["last_result"]
        raise
```

### Strategy 3: Graceful Degradation

```python
async def degraded_mode():
    try:
        return await full_feature_operation()
    except Exception:
        logger.warning("Falling back to limited mode")
        return await limited_feature_operation()
```

## Common Errors

### ForwardingOverrideError

```python
from grafo.errors import ForwardingOverrideError

async def consumer(value: str):
    return value

# This will raise ForwardingOverrideError
node = Node(coroutine=consumer, kwargs=dict(value="preset"))
try:
    await parent.connect(node, forward_as="value")
except ForwardingOverrideError as e:
    print(f"Cannot override existing kwarg: {e}")
```

### NotAsyncCallableError

```python
from grafo.errors import NotAsyncCallableError

async def regular_coroutine():
    return "result"

node = Node(coroutine=regular_coroutine, uuid="node")

try:
    # Trying to use yielding method on non-generator
    await node.run_yielding()
except NotAsyncCallableError as e:
    print(f"Not an async generator: {e}")
```

### MismatchChunkType

```python
from grafo.errors import MismatchChunkType

async def wrong_type():
    return 42  # Returns int

node = Node[str](coroutine=wrong_type, uuid="typed")

try:
    await TreeExecutor(roots=[node]).run()
except MismatchChunkType as e:
    print(f"Type mismatch: {e}")
```

## Next Steps

- [API Reference](../api-reference/exceptions.md) - All exception types
- [Examples](../examples/common-patterns.md) - Error handling patterns
- [Event Callbacks](event-callbacks.md) - Monitor errors with callbacks
