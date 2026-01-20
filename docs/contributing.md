# Contributing to Grafo

Thank you for your interest in contributing to Grafo! This guide will help you get started.

## Getting Started

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/grafo.git
cd grafo
```

### Development Setup

Install Grafo in development mode with all dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `ruff` - Code linting
- `bump2version` - Version management

### Running Tests

Run the full test suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run specific test file:

```bash
pytest tests/test_executor.py
```

Run with print statements visible:

```bash
pytest -s
```

## Code Style

### Linting

Grafo uses `ruff` for linting. Run the linter:

```bash
ruff check grafo/
```

Fix auto-fixable issues:

```bash
ruff check --fix grafo/
```

### Code Formatting

Follow PEP 8 guidelines:

- 4 spaces for indentation (no tabs)
- Maximum line length: 120 characters
- Use meaningful variable names
- Add docstrings to public functions and classes

### Type Hints

Use type hints for all function signatures:

```python
async def my_function(param: str, count: int) -> dict:
    """Function description."""
    return {"param": param, "count": count}
```

## Making Changes

### Branch Naming

Create a descriptive branch name:

```bash
git checkout -b feature/add-new-feature
git checkout -b fix/issue-123
git checkout -b docs/improve-readme
```

### Commit Messages

Write clear, descriptive commit messages:

```
Add feature: Description of the feature

- Bullet point detail 1
- Bullet point detail 2
```

Good commit message examples:
- `feat: Add support for node priorities`
- `fix: Resolve race condition in executor`
- `docs: Update API reference for Node class`
- `test: Add tests for forwarding edge cases`

### Code Changes

1. **Write tests first**: Add tests for new features or bug fixes
2. **Keep changes focused**: One feature/fix per pull request
3. **Update documentation**: Document new features and API changes
4. **Maintain backwards compatibility**: Avoid breaking changes when possible

## Testing

### Writing Tests

Tests are located in the `tests/` directory. Follow existing patterns:

```python
import pytest
from grafo import Node, TreeExecutor

@pytest.mark.asyncio
async def test_my_feature():
    """Test description."""
    # Arrange
    node = Node(coroutine=my_coroutine, uuid="test")

    # Act
    result = await node.run()

    # Assert
    assert result == expected_value
```

### Test Coverage

Aim for high test coverage:

- Test happy paths
- Test error conditions
- Test edge cases
- Test async behavior

### Async Testing

Use `@pytest.mark.asyncio` for async tests:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
async def my_function(param: str, count: int) -> dict:
    """
    Brief description of the function.

    Longer description if needed, explaining the function's behavior,
    use cases, or important details.

    Args:
        param: Description of param
        count: Description of count

    Returns:
        Description of return value

    Raises:
        ValueError: When count is negative
        TypeError: When param is not a string

    Example:
        >>> result = await my_function("test", 5)
        >>> print(result)
        {'param': 'test', 'count': 5}
    """
    if count < 0:
        raise ValueError("count must be non-negative")

    return {"param": param, "count": count}
```

### API Documentation

When adding new public APIs:

1. Add comprehensive docstrings
2. Update relevant documentation pages in `docs/`
3. Add examples to the appropriate guide
4. Update API reference if needed

### Documentation Site

The documentation is built with mkdocs. To build locally:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
mkdocs serve
```

Then visit `http://localhost:8000` to view the docs.

## Pull Request Process

### Before Submitting

1. **Run tests**: Ensure all tests pass
   ```bash
   pytest
   ```

2. **Run linter**: Fix any linting issues
   ```bash
   ruff check --fix grafo/
   ```

3. **Update documentation**: Add/update relevant docs

4. **Add yourself to contributors**: If this is your first contribution

### Submitting

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature
   ```

2. Open a pull request on GitHub

3. Fill out the pull request template with:
   - Description of changes
   - Related issue numbers
   - Testing performed
   - Documentation updates

### Pull Request Guidelines

- **Keep PRs focused**: One feature/fix per PR
- **Write a clear description**: Explain what and why
- **Link related issues**: Reference issue numbers
- **Be responsive**: Address review feedback promptly
- **Keep commits clean**: Squash fixup commits if needed

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, maintainers will merge

## Reporting Issues

### Bug Reports

Include:

- Grafo version
- Python version
- Operating system
- Minimal code to reproduce
- Expected vs actual behavior
- Error messages/stack traces

### Feature Requests

Include:

- Use case description
- Proposed API (if applicable)
- Example usage
- Why this benefits Grafo users

## Development Guidelines

### Design Principles

Remember Grafo's core principles:

1. **Follow established nomenclature**: Use precise, clear terminology
2. **Syntax sugar in moderation**: Keep the API explicit and predictable
3. **Granular programmer control**: Provide fine-grained customization

### Performance Considerations

- Minimize overhead in hot paths
- Avoid unnecessary allocations
- Profile changes that affect execution speed
- Consider scalability for large trees

### Error Handling

- Use custom exceptions for Grafo-specific errors
- Provide clear error messages
- Include context (node UUIDs, parameter names, etc.)
- Document exceptions in docstrings

## Version Management

Grafo uses semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

Version bumping is handled by maintainers using `bump2version`.

## Community

### Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

### Getting Help

- Open an issue for bugs or feature requests
- Discussions for questions and ideas
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors are recognized in:

- GitHub contributors page
- Release notes for significant contributions
- Documentation credits

Thank you for contributing to Grafo!
