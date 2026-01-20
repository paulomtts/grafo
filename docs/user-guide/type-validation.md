# Type Validation

Learn how to use Python generics for runtime type validation in Grafo.

## Overview

Grafo supports generic type parameters for nodes, enabling runtime validation of:

- Regular return values
- Yielded values from async generators
- Type safety across node connections

## Basic Type Validation

### Single Type Parameter

Specify the expected return type when creating a node:

```python
from grafo import Node

async def return_string():
    return "hello"

async def return_number():
    return 42

async def return_list():
    return [1, 2, 3]

# Type-validated nodes
string_node = Node[str](coroutine=return_string, uuid="string")
number_node = Node[int](coroutine=return_number, uuid="number")
list_node = Node[list](coroutine=return_list, uuid="list")
```

### Type Checking

When the node executes, Grafo validates the return type:

```python
async def wrong_type():
    return "string"  # Returns string

# Expect int, but returns str
node = Node[int](coroutine=wrong_type, uuid="wrong")

executor = TreeExecutor(roots=[node])

try:
    await executor.run()
except Exception as e:
    print(f"Type error: {e}")
    # MismatchChunkType exception raised
```

## Validation for Yielded Values

### Async Generator Validation

Type validation works for yielded values:

```python
async def yield_strings():
    yield "first"
    yield "second"
    yield "third"

async def yield_numbers():
    yield 1
    yield 2
    yield 3

# All yields must be strings
string_yielder = Node[str](coroutine=yield_strings, uuid="strings")

# All yields must be integers
number_yielder = Node[int](coroutine=yield_numbers, uuid="numbers")

executor = TreeExecutor(roots=[string_yielder, number_yielder])
await executor.run()  # Success - all yields match types
```

### Mixed Type Yields (Invalid)

All yields from a node must be the same type:

```python
async def mixed_yields():
    yield "string"
    yield 42         # Wrong type!
    yield "another"

node = Node[str](coroutine=mixed_yields, uuid="mixed")

executor = TreeExecutor(roots=[node])

try:
    await executor.run()
except Exception:
    print("Type mismatch detected!")
```

## Complex Types

### Collections

Validate collection types:

```python
async def return_list():
    return [1, 2, 3, 4, 5]

async def return_dict():
    return {"key": "value", "count": 42}

async def return_set():
    return {1, 2, 3, 4}

list_node = Node[list](coroutine=return_list, uuid="list")
dict_node = Node[dict](coroutine=return_dict, uuid="dict")
set_node = Node[set](coroutine=return_set, uuid="set")
```

### Tuples

```python
async def return_tuple():
    return ("name", 42, True)

tuple_node = Node[tuple](coroutine=return_tuple, uuid="tuple")
```

### Custom Classes

```python
class UserData:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

async def return_user():
    return UserData("Alice", 30)

user_node = Node[UserData](coroutine=return_user, uuid="user")
```

## Type Hints vs Grafo Generics

### Python Type Hints

These are for static type checkers (mypy, pyright):

```python
async def typed_function() -> str:
    return "result"
```

### Grafo Generic Parameters

These enable **runtime** validation:

```python
node = Node[str](coroutine=typed_function, uuid="node")
```

### Using Both

Combine them for maximum safety:

```python
async def safe_function() -> str:
    return "result"

# Static checking (mypy) + Runtime validation (Grafo)
node = Node[str](coroutine=safe_function, uuid="safe")
```

## Type Safety Across Connections

### Validated Forwarding

Ensure forwarded data matches parameter types:

```python
async def produce_string() -> str:
    return "data"

async def consume_string(value: str) -> str:
    return f"processed_{value}"

producer = Node[str](coroutine=produce_string, uuid="producer")
consumer = Node[str](coroutine=consume_string, uuid="consumer")

await producer.connect(consumer, forward_as="value")

# Type-safe connection: str → str
```

### Type Mismatches

Grafo doesn't validate forwarding types at connection time, but the receiving function will fail if types don't match:

```python
async def produce_int() -> int:
    return 42

async def consume_string(value: str) -> str:
    return f"processed_{value}"  # Expects string!

producer = Node[int](coroutine=produce_int, uuid="producer")
consumer = Node[str](coroutine=consume_string, uuid="consumer")

await producer.connect(consumer, forward_as="value")

executor = TreeExecutor(roots=[producer])

try:
    await executor.run()
except TypeError:
    print("Type mismatch in forwarding!")
```

## Optional Types

### Handling None

```python
from typing import Optional

async def maybe_return_string() -> Optional[str]:
    import random
    return "value" if random.random() > 0.5 else None

# Accept both str and None
node = Node[Optional[str]](coroutine=maybe_return_string, uuid="maybe")
```

### Union Types

```python
from typing import Union

async def return_str_or_int() -> Union[str, int]:
    import random
    return "string" if random.random() > 0.5 else 42

node = Node[Union[str, int]](coroutine=return_str_or_int, uuid="union")
```

## Generic Type Parameters

### Without Type Validation

If you don't specify a type parameter, no validation occurs:

```python
async def any_return_type():
    return "could be anything"

# No type validation
node = Node(coroutine=any_return_type, uuid="untyped")
```

### When to Use Type Validation

Use type validation when:

1. **Safety is critical**: Prevent type-related runtime errors
2. **APIs with contracts**: Ensure nodes fulfill type contracts
3. **Complex pipelines**: Validate data flow across many nodes
4. **Integration points**: Validate external data sources

Skip type validation for:

1. **Prototyping**: Fast iteration without type constraints
2. **Dynamic types**: Data that genuinely varies in type
3. **Performance**: Minimal overhead, but can skip if needed

## Advanced Type Validation

### Custom Type Validators

While Grafo uses `isinstance()` for validation, you can add custom validation in your coroutines:

```python
from typing import TypeVar, Generic

async def validated_processor(value: int) -> int:
    if not isinstance(value, int):
        raise TypeError(f"Expected int, got {type(value)}")

    if value < 0:
        raise ValueError(f"Value must be non-negative, got {value}")

    return value * 2

node = Node[int](coroutine=validated_processor, uuid="validated")
```

### Dataclass Validation

```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise TypeError("name must be str")
        if not isinstance(self.age, int):
            raise TypeError("age must be int")

async def create_person() -> Person:
    return Person("Alice", 30)

node = Node[Person](coroutine=create_person, uuid="person")
```

## Type Validation with Chunks

When using yielding execution, each chunk is validated:

```python
from grafo import Chunk

async def yield_validated():
    yield 1
    yield 2
    yield 3

node = Node[int](coroutine=yield_validated, uuid="yielder")
executor = TreeExecutor(roots=[node])

async for item in executor.yielding():
    if isinstance(item, Chunk):
        # item.output is guaranteed to be int
        value: int = item.output
        print(f"Validated value: {value}")
```

## Error Messages

### MismatchChunkType Exception

When type validation fails:

```python
from grafo.errors import MismatchChunkType

async def wrong_type():
    return 42  # Returns int

node = Node[str](coroutine=wrong_type, uuid="wrong")

try:
    executor = TreeExecutor(roots=[node])
    await executor.run()
except MismatchChunkType as e:
    print(f"Type mismatch: {e}")
    # Error includes: node UUID, expected type, actual type
```

## Best Practices

1. **Use type hints in coroutines**: Helps with static analysis
2. **Add Grafo generics for runtime validation**: Extra safety layer
3. **Validate at boundaries**: Focus on inputs from external sources
4. **Document type expectations**: Clear comments for complex types
5. **Test with wrong types**: Ensure validation catches errors
6. **Consider performance**: Type checking adds minimal overhead
7. **Use Union types judiciously**: Too many unions reduce type safety

## Common Patterns

### Validated Pipeline

```python
async def extract() -> dict:
    return {"user_id": 123, "name": "Alice"}

async def transform(data: dict) -> str:
    return f"User: {data['name']}"

async def load(result: str) -> bool:
    print(result)
    return True

extract_node = Node[dict](coroutine=extract, uuid="extract")
transform_node = Node[str](coroutine=transform, uuid="transform")
load_node = Node[bool](coroutine=load, uuid="load")

await extract_node.connect(transform_node, forward_as="data")
await transform_node.connect(load_node, forward_as="result")

# Type-safe pipeline: dict → str → bool
```

### Type-Safe Aggregation

```python
async def get_count() -> int:
    return 42

async def get_name() -> str:
    return "Alice"

async def get_active() -> bool:
    return True

async def combine(count: int, name: str, active: bool) -> dict:
    return {"count": count, "name": name, "active": active}

count_node = Node[int](coroutine=get_count, uuid="count")
name_node = Node[str](coroutine=get_name, uuid="name")
active_node = Node[bool](coroutine=get_active, uuid="active")
combine_node = Node[dict](coroutine=combine, uuid="combine")

await count_node.connect(combine_node, forward_as="count")
await name_node.connect(combine_node, forward_as="name")
await active_node.connect(combine_node, forward_as="active")

# All inputs validated before aggregation
```

## Next Steps

- [Event Callbacks](event-callbacks.md) - Hook into node lifecycle
- [Error Handling](error-handling.md) - Robust error management
- [API Reference](../api-reference/node.md) - Complete Node API
- [Examples](../examples/common-patterns.md) - Type-safe patterns
