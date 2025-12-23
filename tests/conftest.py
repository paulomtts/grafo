import asyncio
import logging
from typing import Any, Callable, Optional


from grafo._internal import logger
from grafo import Node

logger.setLevel(logging.DEBUG)


def create_node(
    name: str,
    coroutine: Any,
    timeout: Optional[float] = None,
    on_after_run: Optional[Callable[..., Any]] = None,
    on_after_run_kwargs: Optional[dict[str, Any]] = None,
    kwargs: Optional[dict[str, Any]] = None,
) -> Node:
    """
    Create a node with the given name, coroutine, and picker function.
    """
    node = Node(
        uuid=name,
        coroutine=coroutine,
        timeout=timeout,
        on_after_run=(on_after_run, on_after_run_kwargs) if on_after_run else None,
    )
    node.kwargs = dict(node=node)
    node.kwargs.update(kwargs or {})
    return node


async def mockup_coroutine(node: Node):
    """
    Example coroutine function that simulates a task that takes 1 second to complete.
    """
    await asyncio.sleep(1)
    return f"{node.uuid} result"


async def mockup_picker(node: Node):
    """
    Example picker function that selects the first and third children of the root node.
    """
    logger.info(f" -> picked: {node.children[0].uuid}, {node.children[2].uuid}")
    await node.disconnect(node.children[1])


async def mockup_bad_coroutine(node: Node):
    """
    Example coroutine function that simulates an error.
    """
    raise ValueError(f"{node.uuid} bad coroutine")


async def cycle_coroutine(node: Node, child_node: Node):
    """
    Example coroutine function that simulates a cycle.
    """
    logger.info(f"Cycle coroutine: {node.uuid} -> {child_node.uuid}")
    await node.connect(child_node)
    for grandchild in child_node.children:
        await child_node.disconnect(grandchild)


async def mockup_yielding_coroutine(node: Node):
    """
    Example async generator function that yields intermediate results.
    """
    for i in range(3):
        await asyncio.sleep(0.5)  # Simulate some work
        yield f"{node.uuid} progress {i}"

    # Final result
    await asyncio.sleep(0.5)
    yield f"{node.uuid} completed"

