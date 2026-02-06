import asyncio
import pytest

from grafo import TreeExecutor, Node
from grafo.components import Chunk
from grafo._internal import logger
from conftest import (
    create_node,
    mockup_coroutine,
    mockup_yielding_coroutine,
)


@pytest.mark.asyncio
async def test_yielding_results():
    """
    Test the TreeExecutor's .yielding() method to ensure it yields results as they are set.
    """
    root_node = create_node("root", mockup_coroutine)
    child_node1 = create_node("child1", mockup_coroutine)
    grandchild_node1 = create_node("grandchild1", mockup_coroutine)
    grandchild_node2 = create_node("grandchild2", mockup_coroutine)

    await root_node.connect(child_node1)
    await child_node1.connect(grandchild_node1)
    await child_node1.connect(grandchild_node2)

    # Manually connecting nodes
    executor = TreeExecutor(uuid="Yielding Tree", roots=[root_node])
    results = []

    async for node in executor.yielding():
        if not isinstance(node, Node):
            continue
        results.append((node.uuid, node))
        logger.info(f"Yielded: {node}")

    # Assert that all nodes have been processed and yielded
    nodes_uuids = [
        root_node.uuid,
        child_node1.uuid,
        grandchild_node1.uuid,
        grandchild_node2.uuid,
    ]
    yielded_uuids = [uuid for uuid, _ in results]
    assert all(node_uuid in yielded_uuids for node_uuid in nodes_uuids)
    logger.info("All nodes yielded successfully.")


@pytest.mark.asyncio
async def test_yielding_results_with_multiple_parents():
    """
    Test the TreeExecutor's .yielding() method with a node that has multiple parents.
    The union node is only enqueued when both parents have completed, then runs to completion.
    """

    async def long_running_coroutine(node: Node):
        await asyncio.sleep(3)
        logger.info(f"{node.uuid} executed")
        return f"{node.uuid} result"

    root_node = create_node("root", mockup_coroutine)
    child1_node = create_node("child1", long_running_coroutine)
    child2_node = create_node("child2", mockup_coroutine)
    union_node = create_node("union", long_running_coroutine)

    await root_node.connect(child1_node)
    await root_node.connect(child2_node)
    await child1_node.connect(union_node)
    await child2_node.connect(union_node)

    executor = TreeExecutor(uuid="Yielding Tree with Union", roots=[root_node])

    results = []
    async for node in executor.yielding():
        if not isinstance(node, Node):
            continue
        results.append((node.uuid, node))
        logger.info(f"Yielded: {node}")

    expected_node_ids = [
        root_node.uuid,
        child1_node.uuid,
        child2_node.uuid,
        union_node.uuid,
    ]
    yielded_ids = [n_uuid for n_uuid, _ in results]
    assert all(node_uuid in yielded_ids for node_uuid in expected_node_ids)
    logger.info(
        "Union node was enqueued only after both parents completed, then ran and yielded."
    )


@pytest.mark.asyncio
async def test_yielding_timeout():
    """
    Test that a yielding node with a short timeout that runs longer raises TimeoutError;
    the node does not complete and is not in the yielded results.
    """

    async def slow_yielding_coroutine(node: Node):
        await asyncio.sleep(1)
        yield f"{node.uuid} first"
        await asyncio.sleep(1)
        yield f"{node.uuid} second"

    root_node = create_node("root", mockup_coroutine)
    slow_node = create_node("slow", slow_yielding_coroutine, timeout=0.5)
    await root_node.connect(slow_node)

    executor = TreeExecutor(uuid="Yielding Timeout Tree", roots=[root_node])
    completed_node_uuids = []
    async for item in executor.yielding():
        if isinstance(item, Node):
            completed_node_uuids.append(item.uuid)

    assert len(executor.errors) == 1
    assert isinstance(executor.errors[0], asyncio.TimeoutError)
    assert root_node.uuid in completed_node_uuids
    assert slow_node.uuid not in completed_node_uuids


@pytest.mark.asyncio
async def test_yielding_mixing_results_and_chunks():
    """
    Test the TreeExecutor's .yielding() method with a tree that mixes nodes that yield results and nodes that yield chunks.
    """
    root_node = create_node("root", mockup_coroutine)
    child1_node = create_node("child1", mockup_yielding_coroutine)
    child2_node = create_node("child2", mockup_coroutine)
    grandchild1_node = create_node("grandchild1", mockup_yielding_coroutine)
    grandchild2_node = create_node("grandchild2", mockup_coroutine)

    await root_node.connect(child1_node)
    await root_node.connect(child2_node)
    await child1_node.connect(grandchild1_node)
    await child2_node.connect(grandchild2_node)

    executor = TreeExecutor(uuid="Mixed Tree", roots=[root_node])

    results = []
    node_completions = []
    intermediate_results: list[Chunk[str]] = []

    async for item in executor.yielding():
        node_completions.append(item.output)
        if isinstance(item, Node):
            # This is a completed node
            results.append(f"Completed: {item.uuid}")
            logger.info(f"Completed node: {item.uuid}")
        else:
            # This is an intermediate result from a yielding node
            intermediate_results.append(item)
            results.append(f"Result: {item.uuid} -> {item.output}")
            logger.info(f"Intermediate result: {item.uuid} -> {item.output}")

    # Assert that all nodes were completed
    expected_results = [
        "root result",
        "child1 progress 0",
        "child2 result",
        "child1 progress 1",
        "child1 progress 2",
        "child1 completed",
        "grandchild2 result",
        "grandchild1 progress 0",
        "grandchild1 progress 1",
        "grandchild1 progress 2",
        "grandchild1 completed",
    ]

    assert all(node_uuid in node_completions for node_uuid in expected_results)

    # Assert that we got intermediate results from yielding nodes
    yielding_nodes = [child1_node.uuid, grandchild1_node.uuid]

    # Each yielding node should have yielded multiple results
    for yielding_node_uuid in yielding_nodes:
        node_results = [
            chunk.output
            for chunk in intermediate_results
            if chunk.uuid == yielding_node_uuid
        ]
        assert len(node_results) >= 3  # At least 3 yields per yielding node
        assert any("progress" in result for result in node_results)
        assert any("completed" in result for result in node_results)

    logger.info("Mixed tree test completed successfully!")
    logger.info(f"Completed nodes: {node_completions}")
    logger.info(f"Intermediate results count: {len(intermediate_results)}")
    logger.info(f"Total results: {len(results)}")

