import pytest

from grafo import TreeExecutor, Node
from grafo._internal import logger


@pytest.mark.asyncio
async def test_forwarding_success():
    """
    Test successful forwarding behavior where A -> B -> C, with A forwarding output to B properly,
    and B forwarding output to C without conflicts.
    """
    # Track forwarded values to verify the behavior
    forwarded_values = {}

    async def node_a_coroutine():
        """Node A produces a value and forwards it to B."""
        result = "data_from_A"
        forwarded_values["A"] = result
        return result

    async def node_b_coroutine(data_from_A: str):
        """Node B receives data from A, processes it, and forwards to C."""
        # Verify B received the forwarded data from A
        assert data_from_A == "data_from_A"
        result = f"processed_{data_from_A}"
        forwarded_values["B"] = result
        return result

    async def node_c_coroutine(data_from_B: str, existing_value: str):
        """Node C receives data from B without conflicts."""
        # Verify C received the forwarded data from B
        assert data_from_B == "processed_data_from_A"
        # The existing_value should remain unchanged (it's a different parameter)
        assert existing_value == "original_value"
        result = f"final_{data_from_B}"
        forwarded_values["C"] = result
        return result

    # Create nodes without forwarding configuration in constructor
    node_a = Node(uuid="nodeA", coroutine=node_a_coroutine)
    node_b = Node(uuid="nodeB", coroutine=node_b_coroutine)
    node_c = Node(uuid="nodeC", coroutine=node_c_coroutine)

    # Set up C with only non-conflicting values
    node_c.kwargs["existing_value"] = "original_value"

    # Connect the nodes with forwarding: A -> B -> C
    await node_a.connect(node_b, forward_as="data_from_A")
    await node_b.connect(node_c, forward_as="data_from_B")

    # Create executor and run the tree
    executor = TreeExecutor(uuid="Forwarding Success Test", roots=[node_a])
    result = await executor.run()

    # Assert all nodes were processed
    expected_nodes = [node_a.uuid, node_b.uuid, node_c.uuid]
    assert all(node.uuid in expected_nodes for node in result)
    assert len(result) == len(expected_nodes)

    # Verify the forwarding chain worked correctly
    assert forwarded_values["A"] == "data_from_A"
    assert forwarded_values["B"] == "processed_data_from_A"
    assert forwarded_values["C"] == "final_processed_data_from_A"

    # Verify the final state of node C's kwargs
    assert node_c.kwargs["data_from_B"] == "processed_data_from_A"
    assert node_c.kwargs["existing_value"] == "original_value"


@pytest.mark.asyncio
async def test_forwarding_conflict_error():
    """
    Test forwarding behavior where a conflict occurs when trying to forward to a child
    that already has an argument with the same name.
    """
    # Track forwarded values to verify the behavior
    forwarded_values = {}

    async def node_a_coroutine():
        """Node A produces a value and forwards it to B."""
        result = "data_from_A"
        forwarded_values["A"] = result
        return result

    async def node_b_coroutine(data_from_A: str):
        """Node B receives data from A, processes it, and forwards to C."""
        # Verify B received the forwarded data from A
        assert data_from_A == "data_from_A"
        result = f"processed_{data_from_A}"
        forwarded_values["B"] = result
        return result

    async def node_c_coroutine(data_from_B: str, existing_value: str):
        """Node C receives data from B without conflicts."""
        # Verify C received the forwarded data from B
        assert data_from_B == "processed_data_from_A"
        # The existing_value should remain unchanged (it's a different parameter)
        assert existing_value == "original_value"
        result = f"final_{data_from_B}"
        forwarded_values["C"] = result
        return result

    # Create nodes without forwarding configuration in constructor
    node_a = Node(uuid="nodeA", coroutine=node_a_coroutine)
    node_b = Node(uuid="nodeB", coroutine=node_b_coroutine)
    node_c = Node(uuid="nodeC", coroutine=node_c_coroutine)

    # Set up C with a value that will cause a conflict
    node_c.kwargs["data_from_B"] = "will_raise_error"

    # Connect the nodes with forwarding: A -> B -> C
    await node_a.connect(node_b, forward_as="data_from_A")
    await node_b.connect(node_c, forward_as="data_from_B")

    # Create executor and run the tree
    executor = TreeExecutor(uuid="Forwarding Conflict Test", roots=[node_a])
    result = await executor.run()

    # Assert all nodes were processed
    expected_nodes = [node_a.uuid, node_b.uuid, node_c.uuid]
    assert all(node.uuid in expected_nodes for node in result)
    assert len(result) == 1

    # Verify the forwarding chain worked correctly
    assert forwarded_values["A"] == "data_from_A"
    assert forwarded_values["B"] == "processed_data_from_A"
    assert "C" not in forwarded_values.keys()

    # Verify the final state of node C's kwargs
    assert node_c.kwargs["data_from_B"] == "will_raise_error"


@pytest.mark.asyncio
async def test_on_before_forward_filtering():
    """
    Test using on_before_forward to filter and forward different parts of node A's output
    to different children. Node A outputs two numbers, and each child receives only one
    of them based on the filtering logic.
    """
    # Track forwarded values to verify the behavior
    forwarded_values = {}

    async def node_a_coroutine():
        """Node A produces a tuple of two numbers."""
        result = (42, 100)
        forwarded_values["A"] = result
        return result

    async def node_b_coroutine(first_number: int):
        """Node B receives only the first number from A."""
        # Verify B received only the first number
        assert first_number == 42
        result = f"B processed: {first_number}"
        forwarded_values["B"] = result
        return result

    async def node_c_coroutine(second_number: int):
        """Node C receives only the second number from A."""
        # Verify C received only the second number
        assert second_number == 100
        result = f"C processed: {second_number}"
        forwarded_values["C"] = result
        return result

    # Filter functions for on_before_forward
    async def filter_first_number(forward_data: tuple[int, int]) -> int:
        """Extract only the first number from the tuple."""
        first_num, _ = forward_data
        return first_num

    async def filter_second_number(forward_data: tuple[int, int]) -> int:
        """Extract only the second number from the tuple."""
        _, second_num = forward_data
        return second_num

    # Create nodes
    node_a = Node(uuid="nodeA", coroutine=node_a_coroutine)
    node_b = Node(uuid="nodeB", coroutine=node_b_coroutine)
    node_c = Node(uuid="nodeC", coroutine=node_c_coroutine)

    # Connect A to B with filtering for first number
    await node_a.connect(
        node_b,
        forward_as="first_number",
        on_before_forward=(filter_first_number, None),
    )

    # Connect A to C with filtering for second number
    await node_a.connect(
        node_c, forward_as="second_number", on_before_forward=(filter_second_number, {})
    )

    # Create executor and run the tree
    executor = TreeExecutor(uuid="On Before Forward Filtering Test", roots=[node_a])
    result = await executor.run()

    # Assert all nodes were processed
    expected_nodes = [node_a.uuid, node_b.uuid, node_c.uuid]
    assert all(node.uuid in expected_nodes for node in result)
    assert len(result) == len(expected_nodes)

    # Verify the forwarding chain worked correctly
    assert forwarded_values["A"] == (42, 100)
    assert forwarded_values["B"] == "B processed: 42"
    assert forwarded_values["C"] == "C processed: 100"

    # Verify the final state of each node's kwargs
    assert node_b.kwargs["first_number"] == 42
    assert node_c.kwargs["second_number"] == 100

    logger.info("On before forward filtering test completed successfully!")


@pytest.mark.asyncio
async def test_on_before_forward_with_kwargs():
    """
    Test using on_before_forward with additional kwargs to demonstrate
    more complex filtering scenarios.
    """
    # Track forwarded values to verify the behavior
    forwarded_values = {}

    async def node_a_coroutine():
        """Node A produces a list of numbers."""
        result = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        forwarded_values["A"] = result
        return result

    async def node_b_coroutine(even_numbers: list[int]):
        """Node B receives only even numbers."""
        # Verify B received only even numbers
        assert all(num % 2 == 0 for num in even_numbers)
        result = f"B processed {len(even_numbers)} even numbers: {even_numbers}"
        forwarded_values["B"] = result
        return result

    async def node_c_coroutine(odd_numbers: list[int]):
        """Node C receives only odd numbers."""
        # Verify C received only odd numbers
        assert all(num % 2 == 1 for num in odd_numbers)
        result = f"C processed {len(odd_numbers)} odd numbers: {odd_numbers}"
        forwarded_values["C"] = result
        return result

    # Filter functions with kwargs
    async def filter_even_numbers(forward_data: list[int], **kwargs) -> list[int]:
        """Filter even numbers from the list."""
        max_count = kwargs.get("max_count", len(forward_data))
        even_nums = [num for num in forward_data if num % 2 == 0]
        return even_nums[:max_count]

    async def filter_odd_numbers(forward_data: list[int], **kwargs) -> list[int]:
        """Filter odd numbers from the list."""
        max_count = kwargs.get("max_count", len(forward_data))
        odd_nums = [num for num in forward_data if num % 2 == 1]
        return odd_nums[:max_count]

    # Create nodes
    node_a = Node(uuid="nodeA", coroutine=node_a_coroutine)
    node_b = Node(uuid="nodeB", coroutine=node_b_coroutine)
    node_c = Node(uuid="nodeC", coroutine=node_c_coroutine)

    # Connect A to B with filtering for even numbers (max 3)
    await node_a.connect(
        node_b,
        forward_as="even_numbers",
        on_before_forward=(filter_even_numbers, {"max_count": 3}),
    )

    # Connect A to C with filtering for odd numbers (max 2)
    await node_a.connect(
        node_c,
        forward_as="odd_numbers",
        on_before_forward=(filter_odd_numbers, {"max_count": 2}),
    )

    # Create executor and run the tree
    executor = TreeExecutor(uuid="On Before Forward With Kwargs Test", roots=[node_a])
    result = await executor.run()

    # Assert all nodes were processed
    expected_nodes = [node_a.uuid, node_b.uuid, node_c.uuid]
    assert all(node.uuid in expected_nodes for node in result)
    assert len(result) == len(expected_nodes)

    # Verify the forwarding chain worked correctly
    assert forwarded_values["A"] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert forwarded_values["B"] == "B processed 3 even numbers: [2, 4, 6]"
    assert forwarded_values["C"] == "C processed 2 odd numbers: [1, 3]"

    # Verify the final state of each node's kwargs
    assert node_b.kwargs["even_numbers"] == [2, 4, 6]
    assert node_c.kwargs["odd_numbers"] == [1, 3]

    logger.info("On before forward with kwargs test completed successfully!")

