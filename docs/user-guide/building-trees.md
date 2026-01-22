# Building Trees

Grafo allows you to structure your trees however you want.

!!! info "Cyclic Trees Are Possible"
    Grafo lets you build cycles—even an infinite loop! This means you can connect nodes in a way that creates a cycle within your tree structure, allowing for ongoing, cyclic executions. However, be aware that running such a tree will cause it to execute forever unless you explicitly break the cycle or add some stopping condition in your node logic.


## Common Patterns

### Linear Chain

Sequential execution:

```python
node_1 → node_2 → node_3
```

```python
await node_1.connect(node_2, forward="data")
await node_2.connect(node_3, forward="data")
```

### Fan-out (Parallel Branches)

One parent, multiple parallel children:

```python
       root
      / | \
     a  b  c
```

```python
await root.connect(child_a, forward="data")
await root.connect(child_b, forward="data")
await root.connect(child_c, forward="data")
```

### Fan-in (Merge Results)

Multiple parents converge to one child:

```python
  a   b   c
   \  |  /
      d
```

```python
await node_a.connect(merger, forward="result_a")
await node_b.connect(merger, forward="result_b")
await node_c.connect(merger, forward="result_c")

executor = TreeExecutor(roots=[node_a, node_b, node_c])
```

### Diamond Pattern

Combine fan-out and fan-in:

```python
     root
     /  \
    a    b
     \  /
    merger
```

```python
await root.connect(node_a, forward="data")
await root.connect(node_b, forward="data")
await node_a.connect(merger, forward="result_a")
await node_b.connect(merger, forward="result_b")
```

## Multi-Root Trees

Independent entry points:

```python
root_a = Node(coroutine=task_a, uuid="root_a")
root_b = Node(coroutine=task_b, uuid="root_b")

executor = TreeExecutor(roots=[root_a, root_b])
# Both start simultaneously
```

## Next Steps

- [Forwarding Data](forwarding-data.md) - Pass state between nodes
