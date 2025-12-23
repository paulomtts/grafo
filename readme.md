A simple library for building runnable async trees. Trees are a web of interconnected Nodes, which contain code to be run. **A node can only start executing once all it's parents have finished running.**

## Features
- The number of workers is automatically managed - although you can parametrize this
- Trees can have any shape - including multiple roots - and can be dynamically altered during their runtime
- State can be passed between nodes manually (as lambda functions) or via forwarding
- Yielding coroutines produce `Chunk` objects that wrap intermediate results with the node's UUID

## Installation
- `pip install grafo` to install on your environment
- `pytest` to run tests, add `-s` flag for tests to run `print` statements

## Use

**Basic tree execution**
```python
async def my_coroutine():
    return "result"

root_node = Node(coroutine=my_coroutine, uuid="root")
child_node = Node(coroutine=my_coroutine, uuid="child")

await root_node.connect(child_node)

executor = TreeExecutor(uuid="My Tree", roots=[root_node])
result = await executor.run()
```

**Yielding intermediate results**
```python
async def yielding_coroutine():
    for i in range(3):
        yield f"progress {i}"
    yield "completed"

node = Node(coroutine=yielding_coroutine)
executor = TreeExecutor(roots=[node])

async for item in executor.yielding():
    if isinstance(item, Node):
        print(f"Node {item.uuid} completed")
    else:  # Chunk
        print(f"Intermediate: {item.output}")
```

**Evaluating coroutine kwargs during runtime (manual forwarding)**
```python
node = Node(
    coroutine=my_coroutine,
    kwargs=dict(
        my_arg=lambda: get_dynamic_value()
    )
)
```

**Forwarding output between nodes (automatic forwarding)**
```python
async def producer():
    return "data"

async def consumer(data: str):
    return f"processed_{data}"

node_a = Node(coroutine=producer, uuid="producer")
node_b = Node(coroutine=consumer, uuid="consumer")

await node_a.connect(node_b, forward_as="data")
# node_b will receive node_a's output as the 'data' argument
```

**Type validation with generics**
```python
node = Node[str](coroutine=my_string_coroutine)
# The node will validate that the coroutine returns a string
```

## Developer's Zen
1. Follow established nomenclature: a Node is a Node.
2. Syntax sugar is sweet in moderation.
3. Give the programmer granular control.
