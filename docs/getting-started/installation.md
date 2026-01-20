# Installation

## Requirements

Grafo requires Python 3.6 or higher.

## Install from PyPI

The simplest way to install Grafo is via pip:

```bash
pip install grafo
```

## Install from Source

To install the latest development version from GitHub:

```bash
git clone https://github.com/HappyLoop/grafo.git
cd grafo
pip install -e .
```

## Development Installation

If you want to contribute to Grafo or run tests, install with development dependencies:

```bash
git clone https://github.com/HappyLoop/grafo.git
cd grafo
pip install -e ".[dev]"
```

This installs additional packages:

- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `ruff` - Code linting
- `bump2version` - Version management

## Verify Installation

Verify that Grafo is installed correctly:

```python
import grafo
print(grafo.__version__)  # Should print the version number
```

Or run a quick test:

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

## Running Tests

After installing from source, you can run the test suite:

```bash
pytest
```

Add the `-s` flag to see print statements during test execution:

```bash
pytest -s
```

## Next Steps

Now that you have Grafo installed, continue to the [Quick Start](quick-start.md) guide to build your first async tree.
