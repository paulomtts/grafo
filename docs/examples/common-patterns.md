# Common Patterns

Real-world examples of common patterns using Grafo.

## Data Processing Pipelines

### ETL Pipeline

Extract, Transform, Load pattern:

```python
import asyncio
from grafo import Node, TreeExecutor

async def extract_from_source(source: str):
    """Extract data from various sources."""
    await asyncio.sleep(1)
    print(f"Extracting from {source}")
    return {
        "source": source,
        "records": [{"id": i, "value": f"data_{i}"} for i in range(10)]
    }

async def transform_records(data: dict):
    """Transform extracted data."""
    await asyncio.sleep(0.5)
    print(f"Transforming {len(data['records'])} records")
    return {
        "source": data["source"],
        "records": [
            {**record, "transformed": True, "value": record["value"].upper()}
            for record in data["records"]
        ]
    }

async def validate_data(data: dict):
    """Validate transformed data."""
    await asyncio.sleep(0.3)
    print(f"Validating {len(data['records'])} records")
    valid_records = [r for r in data["records"] if r.get("transformed")]
    return {"source": data["source"], "records": valid_records, "validated": True}

async def load_to_destination(data: dict):
    """Load validated data."""
    await asyncio.sleep(0.5)
    print(f"Loading {len(data['records'])} records to database")
    return f"Loaded {len(data['records'])} records from {data['source']}"

async def main():
    sources = ["database", "api", "files"]

    # Create extraction nodes (roots)
    extractors = [
        Node(
            coroutine=extract_from_source,
            uuid=f"extract_{source}",
            kwargs=dict(source=source)
        )
        for source in sources
    ]

    # Create processing nodes for each source
    for extractor in extractors:
        transformer = Node(coroutine=transform_records, uuid=f"transform_{extractor.uuid}")
        validator = Node(coroutine=validate_data, uuid=f"validate_{extractor.uuid}")
        loader = Node(coroutine=load_to_destination, uuid=f"load_{extractor.uuid}")

        # Build pipeline
        await extractor.connect(transformer, forward_as="data")
        await transformer.connect(validator, forward_as="data")
        await validator.connect(loader, forward_as="data")

    # Execute all pipelines in parallel
    executor = TreeExecutor(uuid="ETL Pipeline", roots=extractors)
    await executor.run()

    print("\nAll ETL pipelines completed!")

asyncio.run(main())
```

## Web Scraping

### Parallel Page Scraping

```python
import asyncio
from grafo import Node, TreeExecutor

async def fetch_page(url: str):
    """Simulate fetching a web page."""
    await asyncio.sleep(1)
    return {"url": url, "html": f"<html>Content from {url}</html>"}

async def parse_page(page_data: dict):
    """Parse HTML and extract data."""
    await asyncio.sleep(0.5)
    return {
        "url": page_data["url"],
        "title": f"Title from {page_data['url']}",
        "links": [f"{page_data['url']}/link{i}" for i in range(5)]
    }

async def extract_links(parsed_data: dict):
    """Extract and process links."""
    await asyncio.sleep(0.3)
    return {"url": parsed_data["url"], "links": parsed_data["links"]}

async def save_results(data: dict):
    """Save extracted data."""
    await asyncio.sleep(0.2)
    print(f"Saved data from {data['url']}: {len(data['links'])} links")
    return f"Saved: {data['url']}"

async def main():
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3",
    ]

    # Create scraping pipeline for each URL
    fetchers = []
    for url in urls:
        fetcher = Node(coroutine=fetch_page, uuid=f"fetch_{url}", kwargs=dict(url=url))
        parser = Node(coroutine=parse_page, uuid=f"parse_{url}")
        extractor = Node(coroutine=extract_links, uuid=f"extract_{url}")
        saver = Node(coroutine=save_results, uuid=f"save_{url}")

        await fetcher.connect(parser, forward_as="page_data")
        await parser.connect(extractor, forward_as="parsed_data")
        await extractor.connect(saver, forward_as="data")

        fetchers.append(fetcher)

    # Execute all scraping tasks in parallel
    executor = TreeExecutor(uuid="Web Scraper", roots=fetchers)
    await executor.run()

    print("\nScraping completed!")

asyncio.run(main())
```

## Batch Processing

### Parallel Batch Jobs

```python
import asyncio
from grafo import Node, TreeExecutor

async def load_batch(batch_id: int, size: int):
    """Load a batch of data."""
    await asyncio.sleep(0.5)
    return {
        "batch_id": batch_id,
        "items": [f"item_{batch_id}_{i}" for i in range(size)]
    }

async def process_batch(batch: dict):
    """Process batch items."""
    for i, item in enumerate(batch["items"]):
        await asyncio.sleep(0.1)
        yield {
            "batch_id": batch["batch_id"],
            "item": item,
            "progress": (i + 1) / len(batch["items"]) * 100
        }

async def aggregate_results(*batches):
    """Aggregate all batch results."""
    total_items = sum(len(b["items"]) for b in batches)
    return {"total_batches": len(batches), "total_items": total_items}

async def main():
    num_batches = 5
    batch_size = 10

    # Create batch processing nodes
    batch_nodes = [
        Node(
            coroutine=process_batch,
            uuid=f"process_batch_{i}",
            kwargs=dict(
                batch=lambda idx=i: load_node.output
                if (load_node := Node(
                    coroutine=load_batch,
                    uuid=f"load_batch_{idx}",
                    kwargs=dict(batch_id=idx, size=batch_size)
                ))
                else None
            )
        )
        for i in range(num_batches)
    ]

    # Create loader nodes
    loaders = []
    processors = []
    for i in range(num_batches):
        loader = Node(
            coroutine=load_batch,
            uuid=f"load_batch_{i}",
            kwargs=dict(batch_id=i, size=batch_size)
        )
        processor = Node(coroutine=process_batch, uuid=f"process_batch_{i}")

        await loader.connect(processor, forward_as="batch")

        loaders.append(loader)
        processors.append(processor)

    # Create aggregator
    aggregator = Node(
        coroutine=aggregate_results,
        uuid="aggregator",
        kwargs=dict(
            **{f"batch_{i}": lambda idx=i: loaders[idx].output for i in range(num_batches)}
        )
    )

    for processor in processors:
        await processor.connect(aggregator)

    # Execute
    executor = TreeExecutor(uuid="Batch Processor", roots=loaders)

    print("Processing batches...")
    async for item in executor.yielding():
        if isinstance(item, Chunk):
            data = item.output
            print(
                f"Batch {data['batch_id']}: {data['item']} "
                f"({data['progress']:.0f}% complete)"
            )

    print(f"\nAggregated results: {aggregator.output}")

asyncio.run(main())
```

## API Request Orchestration

### Parallel API Calls with Aggregation

```python
import asyncio
from grafo import Node, TreeExecutor

async def fetch_user_profile(user_id: int):
    """Fetch user profile."""
    await asyncio.sleep(1)
    return {"user_id": user_id, "name": f"User{user_id}", "email": f"user{user_id}@example.com"}

async def fetch_user_posts(user_id: int):
    """Fetch user posts."""
    await asyncio.sleep(1.5)
    return {"user_id": user_id, "posts": [f"Post{i}" for i in range(5)]}

async def fetch_user_comments(user_id: int):
    """Fetch user comments."""
    await asyncio.sleep(0.8)
    return {"user_id": user_id, "comments": [f"Comment{i}" for i in range(10)]}

async def merge_user_data(profile: dict, posts: dict, comments: dict):
    """Merge all user data."""
    return {
        "user_id": profile["user_id"],
        "name": profile["name"],
        "email": profile["email"],
        "post_count": len(posts["posts"]),
        "comment_count": len(comments["comments"]),
        "posts": posts["posts"][:3],  # First 3 posts
        "comments": comments["comments"][:5]  # First 5 comments
    }

async def main():
    user_id = 123

    # Create API fetch nodes (parallel)
    profile_node = Node(
        coroutine=fetch_user_profile,
        uuid="fetch_profile",
        kwargs=dict(user_id=user_id)
    )

    posts_node = Node(
        coroutine=fetch_user_posts,
        uuid="fetch_posts",
        kwargs=dict(user_id=user_id)
    )

    comments_node = Node(
        coroutine=fetch_user_comments,
        uuid="fetch_comments",
        kwargs=dict(user_id=user_id)
    )

    # Merge node
    merge_node = Node(coroutine=merge_user_data, uuid="merge")

    # Connect (fan-in pattern)
    await profile_node.connect(merge_node, forward_as="profile")
    await posts_node.connect(merge_node, forward_as="posts")
    await comments_node.connect(merge_node, forward_as="comments")

    # Execute
    executor = TreeExecutor(
        uuid="User Data Fetcher",
        roots=[profile_node, posts_node, comments_node]
    )

    print("Fetching user data...")
    await executor.run()

    print(f"\nMerged user data:")
    import json
    print(json.dumps(merge_node.output, indent=2))

asyncio.run(main())
```

## Machine Learning Pipeline

### Model Training and Evaluation

```python
import asyncio
from grafo import Node, TreeExecutor

async def load_dataset(name: str):
    """Load training dataset."""
    await asyncio.sleep(1)
    return {"name": name, "samples": 1000, "features": 20}

async def preprocess_data(dataset: dict):
    """Preprocess dataset."""
    await asyncio.sleep(0.5)
    return {
        **dataset,
        "preprocessed": True,
        "scaled": True
    }

async def split_data(dataset: dict, test_size: float = 0.2):
    """Split into train/test sets."""
    await asyncio.sleep(0.3)
    train_size = int(dataset["samples"] * (1 - test_size))
    test_size = dataset["samples"] - train_size

    return {
        "train": {"samples": train_size, "features": dataset["features"]},
        "test": {"samples": test_size, "features": dataset["features"]}
    }

async def train_model(train_data: dict):
    """Train machine learning model."""
    for epoch in range(1, 6):
        await asyncio.sleep(0.5)
        yield {
            "epoch": epoch,
            "total_epochs": 5,
            "train_samples": train_data["samples"],
            "loss": 1.0 / epoch  # Simulated decreasing loss
        }

async def evaluate_model(test_data: dict):
    """Evaluate trained model."""
    await asyncio.sleep(1)
    return {
        "test_samples": test_data["samples"],
        "accuracy": 0.95,
        "precision": 0.93,
        "recall": 0.94
    }

async def save_model(metrics: dict):
    """Save model and metrics."""
    await asyncio.sleep(0.5)
    print(f"Model saved with accuracy: {metrics['accuracy']:.2%}")
    return "model_saved.pkl"

async def main():
    # Create pipeline
    loader = Node(
        coroutine=load_dataset,
        uuid="load",
        kwargs=dict(name="iris")
    )

    preprocessor = Node(coroutine=preprocess_data, uuid="preprocess")

    splitter = Node(coroutine=split_data, uuid="split")

    trainer = Node(coroutine=train_model, uuid="train")

    evaluator = Node(coroutine=evaluate_model, uuid="evaluate")

    saver = Node(coroutine=save_model, uuid="save")

    # Build pipeline
    await loader.connect(preprocessor, forward_as="dataset")
    await preprocessor.connect(splitter, forward_as="dataset")

    # Extract train/test from split
    trainer.kwargs["train_data"] = lambda: splitter.output["train"]
    evaluator.kwargs["test_data"] = lambda: splitter.output["test"]

    await splitter.connect(trainer)
    await trainer.connect(evaluator)
    await evaluator.connect(saver, forward_as="metrics")

    # Execute with progress monitoring
    executor = TreeExecutor(uuid="ML Pipeline", roots=[loader])

    print("Training model...")
    async for item in executor.yielding():
        if isinstance(item, Chunk):
            data = item.output
            print(
                f"Epoch {data['epoch']}/{data['total_epochs']}: "
                f"Loss = {data['loss']:.4f}"
            )
        elif isinstance(item, Node):
            if item.uuid == "evaluate":
                print(f"\nEvaluation metrics: {item.output}")

    print("\nML pipeline completed!")

asyncio.run(main())
```

## Notification System

### Multi-Channel Notifications

```python
import asyncio
from grafo import Node, TreeExecutor

async def create_notification(event: str, user_id: int):
    """Create notification from event."""
    await asyncio.sleep(0.2)
    return {
        "event": event,
        "user_id": user_id,
        "message": f"User {user_id}: {event} occurred",
        "timestamp": "2024-01-01T00:00:00Z"
    }

async def send_email(notification: dict):
    """Send email notification."""
    await asyncio.sleep(1)
    print(f"📧 Email sent: {notification['message']}")
    return {"channel": "email", "status": "sent"}

async def send_sms(notification: dict):
    """Send SMS notification."""
    await asyncio.sleep(0.8)
    print(f"📱 SMS sent: {notification['message']}")
    return {"channel": "sms", "status": "sent"}

async def send_push(notification: dict):
    """Send push notification."""
    await asyncio.sleep(0.5)
    print(f"🔔 Push sent: {notification['message']}")
    return {"channel": "push", "status": "sent"}

async def log_notification(notification: dict, results: list):
    """Log notification delivery."""
    await asyncio.sleep(0.1)
    channels = [r["channel"] for r in results]
    print(f"📝 Logged: Sent via {', '.join(channels)}")
    return {"logged": True, "channels": channels}

async def main():
    # Create notification
    creator = Node(
        coroutine=create_notification,
        uuid="create",
        kwargs=dict(event="order_placed", user_id=123)
    )

    # Multi-channel delivery (fan-out)
    email_node = Node(coroutine=send_email, uuid="email")
    sms_node = Node(coroutine=send_sms, uuid="sms")
    push_node = Node(coroutine=send_push, uuid="push")

    await creator.connect(email_node, forward_as="notification")
    await creator.connect(sms_node, forward_as="notification")
    await creator.connect(push_node, forward_as="notification")

    # Logger (fan-in)
    logger = Node(
        coroutine=log_notification,
        uuid="logger",
        kwargs=dict(
            notification=lambda: creator.output,
            results=lambda: [email_node.output, sms_node.output, push_node.output]
        )
    )

    await email_node.connect(logger)
    await sms_node.connect(logger)
    await push_node.connect(logger)

    # Execute
    executor = TreeExecutor(uuid="Notification System", roots=[creator])

    print("Sending notifications...\n")
    await executor.run()

    print(f"\nNotification delivery complete!")

asyncio.run(main())
```

## Next Steps

- [Real-World Use Cases](use-cases.md) - More complex examples
- [User Guide](../user-guide/basic-usage.md) - Learn the fundamentals
- [API Reference](../api-reference/node.md) - Complete API documentation
