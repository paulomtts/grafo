import pytest

from grafo import TreeExecutor, Node
from grafo.components import Chunk
from grafo.errors import MismatchChunkType
from grafo._internal import logger


@pytest.mark.asyncio
async def test_type_validation_mismatch():
    """
    Test that a node with a declared generic type raises MismatchChunkType
    when its coroutine returns a value of a different type.
    """

    async def string_coroutine():
        """Coroutine that should return a string but returns an int."""
        return 42  # Wrong type - should be str

    # Create a Node[str] - expects string output
    node = Node[str](
        uuid="type_mismatch_node",
        coroutine=string_coroutine,
    )

    executor = TreeExecutor(uuid="Type Validation Test", roots=[node])
    await executor.run()

    # The executor catches exceptions, so check the errors list
    assert len(executor.errors) == 1
    assert isinstance(executor.errors[0], MismatchChunkType)

    error_message = str(executor.errors[0])
    assert "int" in error_message
    assert "str" in error_message
    assert "type_mismatch_node" in error_message

    logger.info("Type validation mismatch test completed successfully!")


@pytest.mark.asyncio
async def test_type_validation_mismatch_yielding():
    """
    Test that a yielding node with a declared generic type raises MismatchChunkType
    when it yields a Chunk with a different output type.
    """

    async def yielding_coroutine():
        """Yielding coroutine that yields a Chunk with wrong type."""
        yield Chunk[int](
            "type_mismatch_yielding_node", 42
        )  # Wrong type - should be Chunk[str]

    # Create a Node[str] - expects string output
    node = Node[str](
        uuid="type_mismatch_yielding_node",
        coroutine=yielding_coroutine,
    )

    executor = TreeExecutor(uuid="Type Validation Yielding Test", roots=[node])

    # The executor catches exceptions, so collect results and check errors
    results = []
    async for _ in executor.yielding():
        results.append(_)

    # Expect MismatchChunkType to be in the errors list
    assert len(executor.errors) == 1
    assert isinstance(executor.errors[0], MismatchChunkType)

    error_message = str(executor.errors[0])
    assert "int" in error_message
    assert "str" in error_message
    assert "type_mismatch_yielding_node" in error_message

    logger.info("Type validation mismatch yielding test completed successfully!")

