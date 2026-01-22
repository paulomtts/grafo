# Installation

## Requirements

Grafo requires Python 3.10 or higher.

## Install from PyPI

The simplest way to install Grafo is via pip:

```bash
pip install grafo
```

## Verify Installation

```python
import asyncio
from grafo import Node, TreeExecutor

async def hello():
    return "Hello, Grafo!"

async def main():
    node = Node(coroutine=hello, uuid="hello")
    executor = TreeExecutor(uuid="Test", roots=[node])
    await executor.run()
    print(node.output)  # Should print: Hello, Grafo!

asyncio.run(main())
```

## Next Steps

Now that you have Grafo installed, continue to the [Quick Start](quick-start.md) guide to build your first async tree.
