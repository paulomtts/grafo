"""The elastic worker pool must never treat a busy worker as removable.

`__adjust_dynamic_workers`'s shrink branch used `len(self._workers)` -- every
tracked worker, busy ones included -- when deciding how many exit sentinels
to queue. A worker that is still running a node can be targeted for removal
just the same as a genuinely idle one, so a node that becomes ready moments
later can be starved behind that busy worker's work, with nothing live left
to reliably dequeue it. In practice this surfaces as soon as any sibling
lane is held open indefinitely (a pause, a parked resolver, anything that
does not finish on a short clock) while a join becomes ready: the join can
wait arbitrarily long, not just briefly.
"""

import asyncio

import pytest
from conftest import create_node

from grafo import Node, TreeExecutor


@pytest.mark.asyncio
async def test_a_join_is_not_starved_by_an_indefinitely_parked_sibling():
    """A, B feed a real two-parent join C; D is unrelated and does not finish
    on its own -- it parks until C has actually started, which only happens
    once A and B are both done. Before the fix, C's dequeue could be starved
    by the pool's shrink/grow miscounting while D's worker sits busy, and the
    whole tree would hang well past any reasonable deadline. After the fix,
    C starts promptly once ready, releases D, and the tree completes."""
    c_started = asyncio.Event()
    order: list[str] = []

    async def finish(node: Node, delay: float = 0.0) -> str:
        if delay:
            await asyncio.sleep(delay)
        order.append(node.uuid)
        return node.uuid

    async def run_a(node: Node) -> str:
        return await finish(node, 0.05)

    async def run_b(node: Node) -> str:
        return await finish(node, 0.1)

    async def run_c(node: Node) -> str:
        c_started.set()
        return await finish(node)

    async def run_d(node: Node) -> str:
        await asyncio.wait_for(c_started.wait(), timeout=2.0)
        return await finish(node)

    a = create_node("a", run_a)
    b = create_node("b", run_b)
    c = create_node("c", run_c)
    d = create_node("d", run_d)

    await a.connect(c)
    await b.connect(c)

    executor = TreeExecutor(uuid="join-not-starved", roots=[a, b, d])

    await asyncio.wait_for(executor.run(), timeout=5.0)

    assert executor.errors == []
    assert order.count("c") == 1
    assert order.count("d") == 1
    assert order.index("c") < order.index("d")
