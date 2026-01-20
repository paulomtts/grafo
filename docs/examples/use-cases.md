# Real-World Use Cases

Complex real-world examples demonstrating Grafo's capabilities.

## Distributed Task Queue

Build a task queue with parallel workers and progress tracking.

```python
import asyncio
import random
from datetime import datetime
from grafo import Node, TreeExecutor, Chunk
from typing import List

# Task definitions
async def task_coordinator(task_count: int):
    """Create and distribute tasks."""
    await asyncio.sleep(0.5)
    tasks = [
        {"id": i, "type": random.choice(["compute", "io", "network"]), "priority": random.randint(1, 5)}
        for i in range(task_count)
    ]
    print(f"📋 Created {task_count} tasks")
    return tasks

async def worker_process(worker_id: int, task: dict):
    """Process a single task."""
    task_type = task["type"]
    delay = {"compute": 2, "io": 1, "network": 1.5}[task_type]

    # Simulate work with progress updates
    steps = 5
    for step in range(steps):
        await asyncio.sleep(delay / steps)
        yield {
            "worker_id": worker_id,
            "task_id": task["id"],
            "task_type": task_type,
            "step": step + 1,
            "total_steps": steps,
            "progress": (step + 1) / steps * 100
        }

async def collect_results(worker_outputs: List[str]):
    """Aggregate results from all workers."""
    await asyncio.sleep(0.3)
    return {
        "total_tasks": len(worker_outputs),
        "completed_at": datetime.now().isoformat(),
        "status": "success"
    }

async def main():
    num_tasks = 10
    num_workers = 3

    # Create coordinator
    coordinator = Node(
        coroutine=task_coordinator,
        uuid="coordinator",
        kwargs=dict(task_count=num_tasks)
    )

    # Create worker nodes
    workers = []
    for worker_id in range(num_workers):
        # Each worker gets a subset of tasks
        worker = Node(
            coroutine=worker_process,
            uuid=f"worker_{worker_id}",
            kwargs=dict(
                worker_id=worker_id,
                task=lambda wid=worker_id: coordinator.output[wid]
                if wid < len(coordinator.output) else None
            )
        )
        await coordinator.connect(worker)
        workers.append(worker)

    # Results collector
    collector = Node(
        coroutine=collect_results,
        uuid="collector",
        kwargs=dict(
            worker_outputs=lambda: [w.output for w in workers if w.output]
        )
    )

    for worker in workers:
        await worker.connect(collector)

    # Execute with real-time monitoring
    executor = TreeExecutor(uuid="Task Queue", roots=[coordinator])

    print("🚀 Starting task queue...\n")

    task_progress = {}
    async for item in executor.yielding(latency=0.1):
        if isinstance(item, Chunk):
            data = item.output
            task_id = data["task_id"]
            task_progress[task_id] = data["progress"]

            bar = "█" * int(data["progress"] // 10) + "░" * (10 - int(data["progress"] // 10))
            print(
                f"Worker {data['worker_id']} | Task {task_id} ({data['task_type']}): "
                f"[{bar}] {data['progress']:.0f}%"
            )

    print(f"\n✅ All tasks completed!")
    print(f"Results: {collector.output}")

asyncio.run(main())
```

## Microservices Orchestration

Orchestrate multiple microservices with retry logic and fallbacks.

```python
import asyncio
import random
from grafo import Node, TreeExecutor

class ServiceError(Exception):
    """Custom service error."""
    pass

async def auth_service():
    """Authentication service."""
    await asyncio.sleep(0.5)
    if random.random() > 0.9:  # 10% failure rate
        raise ServiceError("Auth service unavailable")
    return {"token": "abc123", "user_id": 42}

async def user_service(auth: dict):
    """User profile service."""
    await asyncio.sleep(0.8)
    if random.random() > 0.85:
        raise ServiceError("User service unavailable")
    return {
        "user_id": auth["user_id"],
        "name": "Alice",
        "email": "alice@example.com",
        "preferences": {"theme": "dark", "language": "en"}
    }

async def order_service(auth: dict):
    """Order history service."""
    await asyncio.sleep(1.0)
    if random.random() > 0.85:
        raise ServiceError("Order service unavailable")
    return {
        "user_id": auth["user_id"],
        "orders": [
            {"id": 1, "total": 99.99, "status": "delivered"},
            {"id": 2, "total": 149.50, "status": "processing"}
        ]
    }

async def recommendation_service(user: dict, orders: dict):
    """Recommendation service."""
    await asyncio.sleep(0.6)
    return {
        "user_id": user["user_id"],
        "recommendations": ["Product A", "Product B", "Product C"]
    }

async def aggregate_response(user: dict, orders: dict, recommendations: dict):
    """Aggregate all service responses."""
    return {
        "user": user,
        "orders": orders["orders"],
        "recommendations": recommendations["recommendations"],
        "personalized": True
    }

async def retry_wrapper(service_func, max_retries=3):
    """Wrapper to add retry logic."""
    async def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                result = await service_func(*args, **kwargs)
                if attempt > 0:
                    print(f"✓ {service_func.__name__} succeeded on attempt {attempt + 1}")
                return result
            except ServiceError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⚠️  {service_func.__name__} failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ {service_func.__name__} failed after {max_retries} attempts")
                    raise
    return wrapper

async def main():
    # Create service nodes with retry logic
    auth_node = Node(
        coroutine=retry_wrapper(auth_service),
        uuid="auth_service",
        timeout=10
    )

    user_node = Node(
        coroutine=retry_wrapper(user_service),
        uuid="user_service",
        timeout=10
    )

    order_node = Node(
        coroutine=retry_wrapper(order_service),
        uuid="order_service",
        timeout=10
    )

    recommendation_node = Node(
        coroutine=retry_wrapper(recommendation_service),
        uuid="recommendation_service",
        timeout=10
    )

    aggregator_node = Node(
        coroutine=aggregate_response,
        uuid="aggregator"
    )

    # Build service dependency tree
    await auth_node.connect(user_node, forward_as="auth")
    await auth_node.connect(order_node, forward_as="auth")

    await user_node.connect(recommendation_node, forward_as="user")
    await order_node.connect(recommendation_node, forward_as="orders")

    await user_node.connect(aggregator_node, forward_as="user")
    await order_node.connect(aggregator_node, forward_as="orders")
    await recommendation_node.connect(aggregator_node, forward_as="recommendations")

    # Execute
    executor = TreeExecutor(uuid="Microservices", roots=[auth_node])

    print("🌐 Orchestrating microservices...\n")

    try:
        await executor.run()

        print(f"\n✅ All services responded successfully!")
        print(f"Aggregated response:")
        import json
        print(json.dumps(aggregator_node.output, indent=2))

    except ServiceError as e:
        print(f"\n❌ Service orchestration failed: {e}")
        if executor.errors:
            print(f"Errors encountered: {executor.errors}")

asyncio.run(main())
```

## Data Science Workflow

Complete data science workflow with data loading, feature engineering, and model comparison.

```python
import asyncio
import random
from grafo import Node, TreeExecutor, Chunk

async def load_dataset(source: str):
    """Load dataset from source."""
    await asyncio.sleep(1)
    return {
        "source": source,
        "rows": 10000,
        "columns": 15,
        "raw_data": [[random.random() for _ in range(15)] for _ in range(100)]
    }

async def clean_data(dataset: dict):
    """Clean and handle missing values."""
    await asyncio.sleep(0.8)
    return {
        **dataset,
        "cleaned": True,
        "missing_handled": True,
        "outliers_removed": True
    }

async def feature_engineering(dataset: dict):
    """Create new features."""
    for feature_idx in range(5):
        await asyncio.sleep(0.3)
        yield {
            "dataset": dataset["source"],
            "feature": f"engineered_feature_{feature_idx}",
            "progress": (feature_idx + 1) / 5 * 100
        }

    # Return final dataset with new features
    yield {
        **dataset,
        "columns": dataset["columns"] + 5,
        "engineered": True
    }

async def train_model(dataset: dict, model_type: str):
    """Train a specific model."""
    epochs = 10
    for epoch in range(epochs):
        await asyncio.sleep(0.2)
        yield {
            "model": model_type,
            "epoch": epoch + 1,
            "total_epochs": epochs,
            "training_accuracy": 0.5 + (epoch / epochs) * 0.45,
            "validation_accuracy": 0.45 + (epoch / epochs) * 0.45
        }

    # Final model performance
    final_accuracy = 0.90 + random.random() * 0.08
    yield {
        "model": model_type,
        "status": "completed",
        "final_accuracy": final_accuracy,
        "final_loss": 0.1 * (1 - final_accuracy)
    }

async def compare_models(*model_results):
    """Compare different models and select best."""
    await asyncio.sleep(0.5)

    models = [
        {"type": result["model"], "accuracy": result["final_accuracy"]}
        for result in model_results
    ]

    best_model = max(models, key=lambda m: m["accuracy"])

    return {
        "models": models,
        "best_model": best_model["type"],
        "best_accuracy": best_model["accuracy"]
    }

async def deploy_model(comparison: dict):
    """Deploy the best model."""
    await asyncio.sleep(1)
    print(f"\n🚀 Deploying {comparison['best_model']} with accuracy {comparison['best_accuracy']:.2%}")
    return {
        "deployed_model": comparison["best_model"],
        "model_url": f"https://api.example.com/models/{comparison['best_model']}",
        "status": "live"
    }

async def main():
    # Data loading and preparation
    loader = Node(
        coroutine=load_dataset,
        uuid="loader",
        kwargs=dict(source="database")
    )

    cleaner = Node(coroutine=clean_data, uuid="cleaner")

    engineer = Node(coroutine=feature_engineering, uuid="engineer")

    await loader.connect(cleaner, forward_as="dataset")
    await cleaner.connect(engineer, forward_as="dataset")

    # Train multiple models in parallel
    model_types = ["random_forest", "gradient_boosting", "neural_network"]
    model_nodes = []

    for model_type in model_types:
        model_node = Node(
            coroutine=train_model,
            uuid=f"train_{model_type}",
            kwargs=dict(
                dataset=lambda: engineer.output,
                model_type=model_type
            )
        )
        await engineer.connect(model_node)
        model_nodes.append(model_node)

    # Model comparison
    comparator = Node(
        coroutine=compare_models,
        uuid="comparator",
        kwargs={
            f"model_{i}": lambda idx=i: model_nodes[idx].output
            for i in range(len(model_nodes))
        }
    )

    for model_node in model_nodes:
        await model_node.connect(comparator)

    # Deployment
    deployer = Node(coroutine=deploy_model, uuid="deployer")
    await comparator.connect(deployer, forward_as="comparison")

    # Execute workflow
    executor = TreeExecutor(uuid="DS Workflow", roots=[loader])

    print("🔬 Starting data science workflow...\n")

    current_phase = None
    async for item in executor.yielding(latency=0.05):
        if isinstance(item, Chunk):
            data = item.output

            # Feature engineering progress
            if "feature" in data:
                if current_phase != "engineering":
                    print("\n🔧 Feature Engineering:")
                    current_phase = "engineering"
                bar = "█" * int(data["progress"] // 5) + "░" * (20 - int(data["progress"] // 5))
                print(f"  [{bar}] {data['progress']:.0f}% - Creating {data['feature']}")

            # Model training progress
            elif "model" in data and "epoch" in data:
                if current_phase != f"training_{data['model']}":
                    print(f"\n🤖 Training {data['model']}:")
                    current_phase = f"training_{data['model']}"
                print(
                    f"  Epoch {data['epoch']}/{data['total_epochs']}: "
                    f"Train Acc: {data['training_accuracy']:.2%}, "
                    f"Val Acc: {data['validation_accuracy']:.2%}"
                )

            # Model completion
            elif "model" in data and data.get("status") == "completed":
                print(f"  ✓ {data['model']} completed - Final accuracy: {data['final_accuracy']:.2%}")

        elif isinstance(item, Node):
            if item.uuid == "comparator":
                print(f"\n📊 Model Comparison:")
                for model in item.output["models"]:
                    marker = "⭐" if model["type"] == item.output["best_model"] else "  "
                    print(f"  {marker} {model['type']}: {model['accuracy']:.2%}")

    print(f"\n✅ Workflow completed!")
    print(f"Deployment status: {deployer.output}")

asyncio.run(main())
```

## CI/CD Pipeline

Continuous integration and deployment pipeline with parallel testing.

```python
import asyncio
import random
from grafo import Node, TreeExecutor, Chunk

async def checkout_code(branch: str):
    """Checkout code from repository."""
    await asyncio.sleep(0.5)
    print(f"📥 Checking out branch: {branch}")
    return {"branch": branch, "commit": "abc123", "files_changed": 15}

async def install_dependencies(code: dict):
    """Install project dependencies."""
    for i in range(3):
        await asyncio.sleep(0.3)
        yield {"phase": "dependencies", "step": i + 1, "total": 3}

    yield {"installed": True, "dependencies": 42}

async def run_linter(code: dict):
    """Run code linter."""
    await asyncio.sleep(1)
    issues = random.randint(0, 5)
    return {"linter": "pylint", "issues": issues, "passed": issues == 0}

async def run_unit_tests(code: dict):
    """Run unit tests."""
    tests = ["test_api", "test_models", "test_utils", "test_services"]
    for i, test in enumerate(tests):
        await asyncio.sleep(0.5)
        passed = random.random() > 0.1
        yield {
            "test_suite": "unit",
            "test": test,
            "passed": passed,
            "progress": (i + 1) / len(tests) * 100
        }

    yield {"test_suite": "unit", "total": len(tests), "passed": True}

async def run_integration_tests(code: dict):
    """Run integration tests."""
    tests = ["test_api_integration", "test_database", "test_external_services"]
    for i, test in enumerate(tests):
        await asyncio.sleep(0.8)
        passed = random.random() > 0.1
        yield {
            "test_suite": "integration",
            "test": test,
            "passed": passed,
            "progress": (i + 1) / len(tests) * 100
        }

    yield {"test_suite": "integration", "total": len(tests), "passed": True}

async def build_docker_image(code: dict):
    """Build Docker image."""
    steps = ["Base image", "Dependencies", "Application", "Cleanup"]
    for i, step in enumerate(steps):
        await asyncio.sleep(0.4)
        yield {"build_step": step, "progress": (i + 1) / len(steps) * 100}

    yield {"image": f"myapp:{code['commit'][:7]}", "size": "234MB", "built": True}

async def run_security_scan(image: dict):
    """Run security vulnerability scan."""
    await asyncio.sleep(1.5)
    vulnerabilities = random.randint(0, 3)
    return {
        "vulnerabilities": vulnerabilities,
        "severity": "low" if vulnerabilities > 0 else "none",
        "passed": vulnerabilities == 0
    }

async def aggregate_results(lint: dict, unit: dict, integration: dict, security: dict):
    """Aggregate all test results."""
    all_passed = all([
        lint["passed"],
        unit["passed"],
        integration["passed"],
        security["passed"]
    ])

    return {
        "all_passed": all_passed,
        "linter": lint,
        "unit_tests": unit,
        "integration_tests": integration,
        "security": security
    }

async def deploy_to_staging(results: dict, image: dict):
    """Deploy to staging environment."""
    if not results["all_passed"]:
        raise Exception("Cannot deploy - tests failed")

    await asyncio.sleep(1)
    print(f"\n🚀 Deploying {image['image']} to staging...")
    return {
        "environment": "staging",
        "url": "https://staging.example.com",
        "deployed": True
    }

async def main():
    # Pipeline setup
    checkout = Node(
        coroutine=checkout_code,
        uuid="checkout",
        kwargs=dict(branch="main")
    )

    dependencies = Node(coroutine=install_dependencies, uuid="dependencies")
    await checkout.connect(dependencies, forward_as="code")

    # Parallel quality checks
    linter = Node(coroutine=run_linter, uuid="linter")
    unit_tests = Node(coroutine=run_unit_tests, uuid="unit_tests")
    integration_tests = Node(coroutine=run_integration_tests, uuid="integration_tests")

    await dependencies.connect(linter, forward_as="code")
    await dependencies.connect(unit_tests, forward_as="code")
    await dependencies.connect(integration_tests, forward_as="code")

    # Build and scan
    builder = Node(coroutine=build_docker_image, uuid="builder")
    await dependencies.connect(builder, forward_as="code")

    scanner = Node(coroutine=run_security_scan, uuid="scanner")
    await builder.connect(scanner, forward_as="image")

    # Aggregate results
    aggregator = Node(
        coroutine=aggregate_results,
        uuid="aggregator",
        kwargs=dict(
            lint=lambda: linter.output,
            unit=lambda: unit_tests.output,
            integration=lambda: integration_tests.output,
            security=lambda: scanner.output
        )
    )

    await linter.connect(aggregator)
    await unit_tests.connect(aggregator)
    await integration_tests.connect(aggregator)
    await scanner.connect(aggregator)

    # Deploy
    deployer = Node(
        coroutine=deploy_to_staging,
        uuid="deployer",
        kwargs=dict(
            results=lambda: aggregator.output,
            image=lambda: builder.output
        )
    )
    await aggregator.connect(deployer)

    # Execute pipeline
    executor = TreeExecutor(uuid="CI/CD Pipeline", roots=[checkout])

    print("🔨 Starting CI/CD pipeline...\n")

    async for item in executor.yielding(latency=0.1):
        if isinstance(item, Chunk):
            data = item.output

            if "phase" in data:
                print(f"📦 Installing dependencies ({data['step']}/{data['total']})...")

            elif "test_suite" in data and "test" in data:
                status = "✓" if data["passed"] else "✗"
                print(f"{status} {data['test_suite'].title()}: {data['test']}")

            elif "build_step" in data:
                print(f"🐳 Building: {data['build_step']} ({data['progress']:.0f}%)")

        elif isinstance(item, Node):
            if item.uuid == "linter":
                status = "✓" if item.output["passed"] else "✗"
                print(f"{status} Linter: {item.output['issues']} issues found")

            elif item.uuid == "scanner":
                status = "✓" if item.output["passed"] else "⚠️"
                print(f"{status} Security scan: {item.output['vulnerabilities']} vulnerabilities")

            elif item.uuid == "aggregator":
                if item.output["all_passed"]:
                    print("\n✅ All checks passed!")
                else:
                    print("\n❌ Some checks failed")

            elif item.uuid == "deployer":
                print(f"✅ Deployed to {item.output['url']}")

    print(f"\n🎉 Pipeline completed!")

asyncio.run(main())
```

## Next Steps

- [Common Patterns](common-patterns.md) - Simpler pattern examples
- [User Guide](../user-guide/basic-usage.md) - Learn the fundamentals
- [API Reference](../api-reference/node.md) - Complete API documentation
