# Error Handling

How Grafo handles errors during tree execution.

## Error Handling in Coroutines

When a node's coroutine raises an exception during execution, the executor:

1. **Catches the exception** in the worker that was executing the node
2. **Stores the error** in `executor.errors` for later inspection
3. **Logs the error** with full traceback information
4. **Stops all workers** immediately by setting the stop event
5. **Prevents further execution** - no additional nodes are processed

The exception is not re-raised from `executor.run()`, but you can check `executor.errors` after execution completes:

```python
async def failing_task():
    raise ValueError("Something went wrong")

node = Node(coroutine=failing_task, uuid="failer")
executor = TreeExecutor(roots=[node])

await executor.run()

if executor.errors:
    for error in executor.errors:
        print(f"Error: {error}")
```

When using `executor.yielding()`, exceptions in coroutines will stop the generator and you can check `executor.errors`:

```python
results = []
async for item in executor.yielding():
    results.append(item)

if executor.errors:
    print(f"Execution stopped with {len(executor.errors)} error(s)")
```

## Grafo-Specific Exceptions

Grafo defines several custom exceptions for framework-specific error conditions.

### SafeExecutionError

Raised when attempting to modify a node that is currently executing. This prevents race conditions and ensures tree structure integrity.

```python
from grafo.errors import SafeExecutionError

node = Node(coroutine=my_task, uuid="task")
executor = TreeExecutor(roots=[node])
run_task = asyncio.create_task(executor.run())

try:
    await node.connect(new_child)  # Modification during execution
except SafeExecutionError as e:
    print(f"Cannot modify running node: {e}")

await run_task
```

### ForwardingOverrideError

Raised when attempting to forward a node's output to a child that already has a keyword argument with the same name.

```python
from grafo.errors import ForwardingOverrideError

child = Node(coroutine=consumer, kwargs=dict(value="preset"))
try:
    await parent.connect(child, forward="value")
except ForwardingOverrideError:
    # Can't override existing kwarg
    pass
```

### ForwardingParameterError

Raised when attempting to forward output to a parameter that the child coroutine cannot accept (unless the child accepts `**kwargs`).

```python
from grafo.errors import ForwardingParameterError

async def child_task(x: int):
    return x + 1

child = Node(coroutine=child_task)
try:
    await parent.connect(child, forward="nonexistent_param")
except ForwardingParameterError:
    # Child doesn't accept this parameter
    pass
```

### AutoForwardError

Raised when `Node.AUTO` forwarding cannot be resolved unambiguously because the child has zero or multiple eligible parameters.

```python
from grafo.errors import AutoForwardError

async def ambiguous_task(x: int, y: int):
    return x + y

child = Node(coroutine=ambiguous_task)
try:
    await parent.connect(child, forward=Node.AUTO)
except AutoForwardError:
    # Multiple eligible parameters, cannot auto-resolve
    pass
```

### MismatchChunkType

Raised when a node's output type doesn't match its declared type parameter during type validation.

```python
from grafo.errors import MismatchChunkType

async def returns_int():
    return 42

node = Node[str](coroutine=returns_int, uuid="wrong")
try:
    await TreeExecutor(roots=[node]).run()
except MismatchChunkType as e:
    print(f"Type mismatch: {e}")
```

### NotAsyncCallableError

Raised when calling a method that expects a specific coroutine type, but the node's coroutine doesn't match.

```python
from grafo.errors import NotAsyncCallableError

async def regular_coroutine():
    return "result"

node = Node(coroutine=regular_coroutine, uuid="regular")
try:
    output = node.output  # OK
    aggregated = node.aggregated_output  # Wrong - not a yielding coroutine
except NotAsyncCallableError:
    # Use output instead of aggregated_output
    pass
```

Also raised when calling `run_yielding()` on a non-yielding coroutine or `run()` on a yielding coroutine:

```python
node = Node(coroutine=regular_coroutine)
try:
    async for chunk in node.run_yielding():
        pass
except NotAsyncCallableError:
    await node.run()  # Use run() for non-yielding coroutines
```

## Next Steps

- [API Reference](../api-reference/exceptions.md) - Complete exception documentation
- [Event Callbacks](event-callbacks.md) - Monitor execution events
