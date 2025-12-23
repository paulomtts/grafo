import random
import pytest

from grafo import TreeExecutor, Node
from grafo._internal import logger
from conftest import (
    create_node,
    mockup_coroutine,
    mockup_picker,
    mockup_bad_coroutine,
    cycle_coroutine,
)


@pytest.mark.asyncio
async def test_simple_tree():
    """
    Test the TreeExecutor using a simple tree structure.
    """
    root_node = create_node("root", mockup_coroutine)
    child_node1 = create_node("child1", mockup_coroutine)
    grandchild_node1 = create_node("grandchild1", mockup_coroutine)
    grandchild_node2 = create_node("grandchild2", mockup_coroutine)

    await root_node.connect(child_node1)
    await child_node1.connect(grandchild_node1)
    await child_node1.connect(grandchild_node2)

    executor = TreeExecutor(uuid="Manual Tree", roots=[root_node])
    result = await executor.run()

    nodes_uuids = [
        root_node.uuid,
        child_node1.uuid,
        grandchild_node1.uuid,
        grandchild_node2.uuid,
    ]
    assert all(node.uuid in nodes_uuids for node in result)
    logger.info(result)


@pytest.mark.asyncio
async def test_picker():
    """
    Test the TreeExecutor using a picker function to build the tree.
    """
    root_node = create_node("root", mockup_picker)
    child_node1 = create_node("child1", mockup_coroutine)
    child_node2 = create_node("child2", mockup_coroutine)
    child_node3 = create_node("child3", mockup_coroutine)

    await root_node.connect(child_node1)
    await root_node.connect(child_node2)
    await root_node.connect(child_node3)

    executor = TreeExecutor(uuid="Picker Tree", roots=[root_node])
    result = await executor.run()

    nodes_uuids = [
        root_node.uuid,
        child_node1.uuid,
        child_node3.uuid,
    ]
    assert all(node.uuid in nodes_uuids for node in result)
    assert child_node2.uuid not in nodes_uuids
    logger.info(result)


@pytest.mark.asyncio
async def test_union():
    """
    Test the TreeExecutor for when a single node
    """
    root_node = create_node("root", mockup_coroutine)
    child_node1 = create_node("child1", mockup_coroutine)
    child_node2 = create_node("child2", mockup_coroutine)
    union_node = create_node("union", mockup_coroutine)

    await root_node.connect(child_node1)
    await root_node.connect(child_node2)
    await child_node1.connect(union_node)
    await child_node2.connect(union_node)

    executor = TreeExecutor(uuid="Union Tree", roots=[root_node])
    result = await executor.run()

    nodes_uuids = [
        root_node.uuid,
        child_node1.uuid,
        child_node2.uuid,
        union_node.uuid,
    ]
    assert all(node.uuid in nodes_uuids for node in result)
    assert len(result) == len(nodes_uuids)
    logger.info(result)


@pytest.mark.asyncio
async def test_error():
    """
    Test the TreeExecutor with an error in a node.
    """
    root_node = create_node("root", mockup_coroutine)
    child_node1 = create_node("child1", mockup_coroutine)
    child_node2 = create_node("child2", mockup_bad_coroutine)
    grandchild_node1 = create_node("grandchild1", mockup_coroutine)
    grandchild_node2 = create_node("grandchild2", mockup_coroutine)

    await root_node.connect(child_node1)
    await root_node.connect(child_node2)
    await child_node1.connect(grandchild_node1)
    await child_node2.connect(grandchild_node2)

    executor = TreeExecutor(uuid="Error Tree", roots=[root_node])
    result = await executor.run()

    # Assert result
    nodes_uuids = [root_node.uuid, child_node1.uuid, grandchild_node1.uuid]
    assert all(node.uuid in nodes_uuids for node in result)
    assert child_node2.uuid not in nodes_uuids
    assert grandchild_node2.uuid not in nodes_uuids


@pytest.mark.asyncio
async def test_multiple_roots_structure():
    """
    Test a tree structure with multiple root nodes, each with their own children.
    This tests the executor's ability to process trees without a single root node.
    """
    # Create nodes
    root1_node = create_node("root1", mockup_coroutine)
    root2_node = create_node("root2", mockup_coroutine)
    child1_node = create_node("child1", mockup_coroutine)
    child2_node = create_node("child2", mockup_coroutine)
    grandchild1_node = create_node("grandchild1", mockup_coroutine)
    grandchild2_node = create_node("grandchild2", mockup_coroutine)
    grandchild3_node = create_node("grandchild3", mockup_coroutine)
    grandchild4_node = create_node("grandchild4", mockup_coroutine)

    await root1_node.connect(child1_node)
    await root2_node.connect(child2_node)
    await child1_node.connect(grandchild1_node)
    await child1_node.connect(grandchild2_node)
    await child2_node.connect(grandchild3_node)
    await child2_node.connect(grandchild4_node)

    # Create executor and build the tree
    executor = TreeExecutor(uuid="Multiple Roots Tree", roots=[root1_node, root2_node])
    result = await executor.run()

    # Assert all nodes were processed
    expected_nodes = [
        root1_node.uuid,
        root2_node.uuid,
        child1_node.uuid,
        child2_node.uuid,
        grandchild1_node.uuid,
        grandchild2_node.uuid,
        grandchild3_node.uuid,
        grandchild4_node.uuid,
    ]

    # Check that all expected nodes are in the result
    assert all(node.uuid in expected_nodes for node in result)
    assert len(result) == len(expected_nodes)

    logger.info(f"Multiple roots test completed with {len(result)} nodes processed")


@pytest.mark.asyncio
async def test_manual_cycle():
    """
    Test a cycle in the tree structure with nodeA -> nodeB -> nodeA and then break the cycle.
    """
    # Create nodes
    node_a = create_node("nodeA", mockup_coroutine)
    node_b = create_node("nodeB", cycle_coroutine, kwargs={"child_node": node_a})

    # Connect nodes to form a cycle
    await node_a.connect(node_b)

    # Create executor and run the tree
    executor = TreeExecutor(uuid="Cycle Break Tree", roots=[node_a])
    result = await executor.run()

    # Assert that the cycle was broken and nodes were processed
    nodes_uuids = [node_a.uuid, node_b.uuid]
    assert all(node.uuid in nodes_uuids for node in result)
    logger.info("Cycle break test completed with nodes processed successfully.")


@pytest.mark.asyncio
async def test_dynamic_cycle_connection():
    """
    Test dynamic cycle creation and breaking during runtime.
    Node A outputs random floats, Node B creates a cycle with A, lets A run again,
    then breaks the cycle.
    """
    total_a_runs = 0
    node_a_first_output = None
    node_a_second_output = None

    async def random_float_coroutine(node: Node, target_node: Node):
        """
        Coroutine that outputs a random float between 0 and 1.
        """
        nonlocal total_a_runs, node_a_first_output, node_a_second_output
        number = random.random()
        if total_a_runs > 0:
            await node.disconnect(target_node)
            node_a_second_output = number
        else:
            node_a_first_output = number

        print(f"{node.uuid} generated number: {number}")
        total_a_runs += 1
        return number

    async def cycle_creator_coroutine(node: Node, target_node: Node):
        """
        Coroutine that creates a cycle with the target node, waits for it to run,
        then breaks the cycle.
        """
        await node.connect(target_node)
        return f"{node.uuid} cycle completed"

    # Create nodes
    node_a = create_node("nodeA", random_float_coroutine)
    node_b = create_node("nodeB", cycle_creator_coroutine)
    node_a.kwargs = dict(node=node_a, target_node=node_b)
    node_b.kwargs = dict(node=node_b, target_node=node_a)

    # Initial connection A -> B
    await node_a.connect(node_b)

    # Create executor and run the tree
    executor = TreeExecutor(uuid="Dynamic Cycle Tree", roots=[node_a])
    result = await executor.run()

    # Assert that both nodes were processed
    nodes_uuids = [node_a.uuid, node_b.uuid]
    assert all(node.uuid in nodes_uuids for node in result)

    # Verify that node A's first output is not equal to its second output
    assert node_a_first_output != node_a_second_output

    print("Dynamic cycle test completed successfully")

