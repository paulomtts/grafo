import pytest

from grafo import TreeExecutor
from grafo._internal import logger
from conftest import create_node, mockup_coroutine


@pytest.mark.asyncio
async def test_repr_two_roots_conjoined():
    """
    Test the __repr__ method of TreeExecutor with a tree that has 2 roots
    that eventually become conjoined through a shared child node.
    """
    # Create nodes for the first root branch
    root1_node = create_node("root1", mockup_coroutine)
    child1_node = create_node("child1", mockup_coroutine)
    grandchild1_node = create_node("grandchild1", mockup_coroutine)

    # Create nodes for the second root branch
    root2_node = create_node("root2", mockup_coroutine)
    child2_node = create_node("child2", mockup_coroutine)

    # Create the shared node where the two branches conjoin
    shared_node = create_node("shared", mockup_coroutine)
    final_node = create_node("final", mockup_coroutine)

    # Connect first branch: root1 -> child1 -> grandchild1 -> shared
    await root1_node.connect(child1_node)
    await child1_node.connect(grandchild1_node)
    await grandchild1_node.connect(shared_node)

    # Connect second branch: root2 -> child2 -> shared
    await root2_node.connect(child2_node)
    await child2_node.connect(shared_node)

    # Connect shared node to final node
    await shared_node.connect(final_node)

    # Create executor with both roots
    executor = TreeExecutor(
        uuid="Conjoined Tree Test",
        description="A tree with two roots that conjoin at a shared node",
        roots=[root1_node, root2_node],
    )

    # Get the string representation
    tree_repr = repr(executor)

    # Print the representation for visual verification
    print("\n" + "=" * 50)
    print("TREE REPRESENTATION:")
    print("=" * 50)
    print(tree_repr)
    print("=" * 50)

    # Assert the representation contains expected elements
    assert "UUID: Conjoined Tree Test" in tree_repr
    assert (
        "Description: A tree with two roots that conjoin at a shared node" in tree_repr
    )
    assert "Structure:" in tree_repr

    # Assert both roots are present
    assert "Root root1:" in tree_repr
    assert "Root root2:" in tree_repr

    # Assert the connections from root1 branch
    assert "root1 -> child1" in tree_repr
    assert "child1 -> grandchild1" in tree_repr
    assert "grandchild1 -> shared" in tree_repr

    # Assert the connections from root2 branch
    assert "root2 -> child2" in tree_repr
    assert "child2 -> shared" in tree_repr

    # Assert the shared node connections
    assert "shared -> final" in tree_repr

    # Verify the structure is correct by running the tree
    result = await executor.run()

    # Assert all nodes were processed
    expected_nodes = [
        root1_node.uuid,
        root2_node.uuid,
        child1_node.uuid,
        child2_node.uuid,
        grandchild1_node.uuid,
        shared_node.uuid,
        final_node.uuid,
    ]

    assert all(node.uuid in expected_nodes for node in result)
    assert len(result) == len(expected_nodes)

    logger.info("Conjoined tree representation test completed successfully!")


@pytest.mark.asyncio
async def test_get_output_nodes():
    """
    Test the get_output_nodes method of TreeExecutor to ensure it correctly
    identifies all leaf nodes (nodes with no children) in the tree.
    """
    # Create a complex tree structure with multiple leaf nodes
    root_node = create_node("root", mockup_coroutine)

    # First branch: root -> child1 -> leaf1
    child1_node = create_node("child1", mockup_coroutine)
    leaf1_node = create_node("leaf1", mockup_coroutine)

    # Second branch: root -> child2 -> leaf2, leaf3
    child2_node = create_node("child2", mockup_coroutine)
    leaf2_node = create_node("leaf2", mockup_coroutine)
    leaf3_node = create_node("leaf3", mockup_coroutine)

    # Third branch: root -> child3 -> grandchild -> leaf4
    child3_node = create_node("child3", mockup_coroutine)
    grandchild_node = create_node("grandchild", mockup_coroutine)
    leaf4_node = create_node("leaf4", mockup_coroutine)

    # Fourth branch: root -> leaf5 (direct leaf)
    leaf5_node = create_node("leaf5", mockup_coroutine)

    # Connect the tree
    await root_node.connect(child1_node)
    await root_node.connect(child2_node)
    await root_node.connect(child3_node)
    await root_node.connect(leaf5_node)

    await child1_node.connect(leaf1_node)
    await child2_node.connect(leaf2_node)
    await child2_node.connect(leaf3_node)
    await child3_node.connect(grandchild_node)
    await grandchild_node.connect(leaf4_node)

    # Create executor
    executor = TreeExecutor(
        uuid="Output Nodes Test",
        description="Testing get_output_nodes method",
        roots=[root_node],
    )

    # Get the output nodes (leaf nodes)
    output_nodes = executor.get_leaves()

    # Print the output nodes for verification
    print("\n" + "=" * 50)
    print("OUTPUT NODES (LEAF NODES):")
    print("=" * 50)
    for node in output_nodes:
        print(f"Leaf node: {node.uuid}")
    print("=" * 50)

    # Expected leaf nodes
    expected_leaf_nodes = [
        leaf1_node.uuid,
        leaf2_node.uuid,
        leaf3_node.uuid,
        leaf4_node.uuid,
        leaf5_node.uuid,
    ]

    # Assert we got the correct number of leaf nodes
    assert len(output_nodes) == len(expected_leaf_nodes)

    # Assert all expected leaf nodes are present
    output_node_uuids = [node.uuid for node in output_nodes]
    assert all(leaf_uuid in output_node_uuids for leaf_uuid in expected_leaf_nodes)

    # Assert that non-leaf nodes are NOT in the output
    non_leaf_nodes = [
        root_node.uuid,
        child1_node.uuid,
        child2_node.uuid,
        child3_node.uuid,
        grandchild_node.uuid,
    ]
    assert all(
        non_leaf_uuid not in output_node_uuids for non_leaf_uuid in non_leaf_nodes
    )

    # Test with multiple roots
    root2_node = create_node("root2", mockup_coroutine)
    leaf6_node = create_node("leaf6", mockup_coroutine)
    await root2_node.connect(leaf6_node)

    executor_multi_root = TreeExecutor(
        uuid="Multi-Root Output Nodes Test",
        description="Testing get_output_nodes with multiple roots",
        roots=[root_node, root2_node],
    )

    # Get output nodes for multi-root tree
    multi_output_nodes = executor_multi_root.get_leaves()

    # Expected leaf nodes for multi-root tree
    expected_multi_leaf_nodes = expected_leaf_nodes + [leaf6_node.uuid]

    # Assert we got the correct number of leaf nodes
    assert len(multi_output_nodes) == len(expected_multi_leaf_nodes)

    # Assert all expected leaf nodes are present
    multi_output_node_uuids = [node.uuid for node in multi_output_nodes]
    assert all(
        leaf_uuid in multi_output_node_uuids for leaf_uuid in expected_multi_leaf_nodes
    )

    # Test with a tree that has a single node (root is also a leaf)
    single_node = create_node("single", mockup_coroutine)
    executor_single = TreeExecutor(
        uuid="Single Node Test",
        description="Testing get_output_nodes with a single node",
        roots=[single_node],
    )

    single_output_nodes = executor_single.get_leaves()
    assert len(single_output_nodes) == 1
    assert single_output_nodes[0].uuid == single_node.uuid

    logger.info("get_output_nodes test completed successfully!")
