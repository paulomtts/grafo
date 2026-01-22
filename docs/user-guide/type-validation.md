# Type Validation

Runtime type validation using Python generics.

## Basic Type Validation

Specify expected return type:

```python
from grafo import Node

async def return_string():
    return "text"

async def return_number():
    return 42

# Type-validated nodes
string_node = Node[str](coroutine=return_string, uuid="string")
number_node = Node[int](coroutine=return_number, uuid="number")
```


## Complex Types

### Collections

```python
async def return_list():
    return [1, 2, 3]

async def return_dict():
    return {"key": "value"}

list_node = Node[list](coroutine=return_list, uuid="list")
dict_node = Node[dict](coroutine=return_dict, uuid="dict")
```

### Custom Classes

```python
class UserData:
    def __init__(self, name: str):
        self.name = name

async def return_user():
    return UserData("Alice")

user_node = Node[UserData](coroutine=return_user, uuid="user")
```

## Optional Types

Handle None values:

```python
from typing import Optional

async def maybe_return():
    return None  # or "value"

node = Node[Optional[str]](coroutine=maybe_return, uuid="maybe")
```

## Union Types

```python
from typing import Union

async def return_str_or_int():
    return "string"  # or 42

node = Node[Union[str, int]](coroutine=return_str_or_int, uuid="union")
```

## Without Type Validation

Omit type parameter for no validation:

```python
node = Node(coroutine=any_return_type, uuid="untyped")
# No runtime validation
```

## Next Steps

- [Event Callbacks](event-callbacks.md) - Hook into node lifecycle
- [Error Handling](error-handling.md) - Handle type errors
