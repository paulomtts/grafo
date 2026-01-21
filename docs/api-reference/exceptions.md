# Exceptions API Reference

Complete documentation for Grafo's custom exceptions.

## Overview

Grafo defines several custom exceptions for specific error conditions:

- `SafeExecutionError` - Node modified during execution
- `NotAsyncCallableError` - Wrong coroutine type for method
- `ForwardingOverrideError` - Forwarding conflicts with existing kwargs
- `MismatchChunkType` - Type validation failure

## SafeExecutionError

### Description

Raised when attempting to modify a node that is currently executing.

This prevents race conditions and ensures tree structure integrity during execution.

### Signature

```python
class SafeExecutionError(Exception):
    """Raised when a node is modified during its execution."""
```

### When Raised

- Connecting a child to a running node
- Disconnecting a child from a running node
- Redirecting children of a running node

### Example

```python
import asyncio
from grafo import Node, TreeExecutor
from grafo.errors import SafeExecutionError

async def long_task():
    await asyncio.sleep(10)
    return "done"

async def modify_during_execution():
    node = Node(coroutine=long_task, uuid="long")
    executor = TreeExecutor(roots=[node])

    # Start execution
    run_task = asyncio.create_task(executor.run())

    # Try to modify while running
    try:
        new_child = Node(coroutine=some_task, uuid="child")
        await node.connect(new_child)
    except SafeExecutionError as e:
        print(f"Cannot modify running node: {e}")

    await run_task

asyncio.run(modify_during_execution())
```

### Prevention

Wait for execution to complete before modifying:

```python
await executor.run()  # Wait for completion

# Now safe to modify
await node.connect(new_child)
```

---

## NotAsyncCallableError

### Description

Raised when calling a method that expects a specific coroutine type, but the node's coroutine doesn't match.

### Signature

```python
class NotAsyncCallableError(Exception):
    """Raised when a method is called on the wrong coroutine type."""
```

### When Raised

- Calling `run_yielding()` on a node with a regular async function (not a generator)
- Calling `run()` on a node with an async generator (should use `run_yielding()`)

### Example

```python
from grafo import Node
from grafo.errors import NotAsyncCallableError

async def regular_coroutine():
    return "result"  # Not a generator

node = Node(coroutine=regular_coroutine, uuid="regular")

try:
    # Trying to use yielding method on regular coroutine
    async for chunk in node.run_yielding():
        print(chunk)
except NotAsyncCallableError as e:
    print(f"Wrong coroutine type: {e}")
```

### Solution

Use the appropriate method:

```python
# For regular coroutines
result = await node.run()

# For async generators
async for chunk in node.run_yielding():
    print(chunk.output)
```

Or use `TreeExecutor` which handles both:

```python
executor = TreeExecutor(roots=[node])

# Works with both regular and yielding nodes
async for item in executor.yielding():
    if isinstance(item, Chunk):
        print(item.output)
    elif isinstance(item, Node):
        print(f"{item.uuid} completed")
```

---

## ForwardingOverrideError

### Description

Raised when attempting to forward data to a parameter that already has a value in the node's kwargs.

This prevents accidental overwriting of explicitly set parameters.

### Signature

```python
class ForwardingOverrideError(Exception):
    """Raised when forwarding would override an existing kwarg."""
```

### When Raised

- Using `forward="param"` when `param` is already in the node's kwargs

### Example

```python
from grafo import Node
from grafo.errors import ForwardingOverrideError

async def producer():
    return "data"

async def consumer(value: str):
    return f"processed_{value}"

parent = Node(coroutine=producer, uuid="parent")

# Child already has 'value' set
child = Node(
    coroutine=consumer,
    uuid="child",
    kwargs=dict(value="preset_value")  # Pre-set value
)

try:
    # Try to forward to the same parameter
    await parent.connect(child, forward="value")
except ForwardingOverrideError as e:
    print(f"Forwarding conflict: {e}")
```

### Solutions

**Option 1**: Remove the pre-set value

```python
child = Node(coroutine=consumer, uuid="child")
await parent.connect(child, forward="value")
```

**Option 2**: Use a different parameter name

```python
async def consumer(value: str, other_value: str):
    return f"{value} and {other_value}"

child = Node(
    coroutine=consumer,
    uuid="child",
    kwargs=dict(value="preset_value")
)

await parent.connect(child, forward="other_value")
```

**Option 3**: Use manual forwarding with lambda

```python
child = Node(
    coroutine=consumer,
    uuid="child",
    kwargs=dict(
        value=lambda: parent.output  # Manual forwarding
    )
)

await parent.connect(child)  # No forwarding
```

---

## MismatchChunkType

### Description

Raised when a node's output doesn't match its declared generic type parameter.

Enables runtime type validation for type-safe trees.

### Signature

```python
class MismatchChunkType(Exception):
    """Raised when output type doesn't match the declared type parameter."""
```

### When Raised

- Node with type parameter `Node[T]` returns a value that's not type `T`
- Yielding node with type parameter `Node[T]` yields a value that's not type `T`

### Example

```python
from grafo import Node, TreeExecutor
from grafo.errors import MismatchChunkType

async def return_wrong_type():
    return 42  # Returns int

# Declare as returning str
node = Node[str](coroutine=return_wrong_type, uuid="typed")

executor = TreeExecutor(roots=[node])

try:
    await executor.run()
except MismatchChunkType as e:
    print(f"Type mismatch: {e}")
    # Error message includes:
    # - Node UUID
    # - Expected type (str)
    # - Actual type (int)
```

### With Yielding

```python
async def yield_mixed_types():
    yield "string"  # OK
    yield 42        # Wrong type!
    yield "another"

node = Node[str](coroutine=yield_mixed_types, uuid="yielder")

try:
    async for chunk in node.run_yielding():
        print(chunk.output)
except MismatchChunkType as e:
    print(f"Type mismatch on yield: {e}")
```

### Solutions

**Option 1**: Fix the return type

```python
async def return_correct_type():
    return "string"  # Returns str

node = Node[str](coroutine=return_correct_type, uuid="typed")
```

**Option 2**: Change the type parameter

```python
async def return_number():
    return 42

node = Node[int](coroutine=return_number, uuid="typed")
```

**Option 3**: Remove type validation

```python
async def return_anything():
    return 42

# No type parameter = no validation
node = Node(coroutine=return_anything, uuid="untyped")
```

**Option 4**: Use Union types

```python
from typing import Union

async def return_str_or_int():
    return 42  # or "string"

node = Node[Union[str, int]](coroutine=return_str_or_int, uuid="union")
```

---

## Exception Hierarchy

```
Exception (built-in)
├── SafeExecutionError
├── NotAsyncCallableError
├── ForwardingOverrideError
└── MismatchChunkType
```

All Grafo exceptions inherit directly from Python's base `Exception` class.

## Catching Grafo Exceptions

### Catch Specific Exceptions

```python
from grafo.errors import (
    SafeExecutionError,
    ForwardingOverrideError,
    MismatchChunkType,
    NotAsyncCallableError
)

try:
    await executor.run()
except SafeExecutionError as e:
    logger.error(f"Execution conflict: {e}")
except ForwardingOverrideError as e:
    logger.error(f"Forwarding error: {e}")
except MismatchChunkType as e:
    logger.error(f"Type error: {e}")
except NotAsyncCallableError as e:
    logger.error(f"Wrong coroutine type: {e}")
```

### Catch All Grafo Exceptions

Since there's no common base class, catch them individually:

```python
from grafo.errors import (
    SafeExecutionError,
    ForwardingOverrideError,
    MismatchChunkType,
    NotAsyncCallableError
)

GRAFO_EXCEPTIONS = (
    SafeExecutionError,
    ForwardingOverrideError,
    MismatchChunkType,
    NotAsyncCallableError
)

try:
    await executor.run()
except GRAFO_EXCEPTIONS as e:
    logger.error(f"Grafo error: {type(e).__name__}: {e}")
```

## Best Practices

1. **Catch specific exceptions**: Handle each error type appropriately
2. **Log with context**: Include node UUIDs and relevant details
3. **Fail fast for logic errors**: `ForwardingOverrideError` and `NotAsyncCallableError` indicate programming errors
4. **Handle runtime errors gracefully**: `SafeExecutionError` can occur in concurrent scenarios
5. **Validate types early**: Use type parameters to catch `MismatchChunkType` during development

## Complete Example

```python
import asyncio
import logging
from grafo import Node, TreeExecutor, Chunk
from grafo.errors import (
    SafeExecutionError,
    ForwardingOverrideError,
    MismatchChunkType,
    NotAsyncCallableError
)

logger = logging.getLogger(__name__)

async def safe_execution_example():
    """Handle all Grafo exceptions gracefully."""

    try:
        # Build tree
        async def task_a() -> str:
            return "result"

        async def task_b(data: str) -> str:
            return f"processed_{data}"

        node_a = Node[str](coroutine=task_a, uuid="a")
        node_b = Node[str](coroutine=task_b, uuid="b")

        # Connect with forwarding
        await node_a.connect(node_b, forward="data")

        # Execute
        executor = TreeExecutor(uuid="Safe Tree", roots=[node_a])
        await executor.run()

        logger.info("Execution successful")

    except ForwardingOverrideError as e:
        logger.error(f"Forwarding conflict: {e}")
        # Fix: Check node kwargs before forwarding

    except MismatchChunkType as e:
        logger.error(f"Type validation failed: {e}")
        # Fix: Ensure coroutines return correct types

    except NotAsyncCallableError as e:
        logger.error(f"Wrong coroutine type: {e}")
        # Fix: Use correct method (run vs run_yielding)

    except SafeExecutionError as e:
        logger.error(f"Execution conflict: {e}")
        # Fix: Don't modify nodes during execution

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise

asyncio.run(safe_execution_example())
```

## See Also

- [Error Handling Guide](../user-guide/error-handling.md) - Comprehensive error handling patterns
- [Node API](node.md) - Node methods that raise exceptions
- [TreeExecutor API](executor.md) - Executor error tracking
