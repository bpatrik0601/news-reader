import argparse
import yaml

import config
from pipelines.news_pipeline import NewsPipeline


def load_config():
    with open("config/sources.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_topic(config: dict, cli_topic: str | None) -> str:
    if cli_topic:
        print(f"[Main] Using topic from CLI: {cli_topic}")
        return cli_topic

    topic_cfg = config.get("topic", {})

    if "queries" in topic_cfg:
        return topic_cfg["queries"]

    if "query" in topic_cfg:
        return topic_cfg["query"]

    raise RuntimeError(
        "No topic specified. Use --topic or define topic.query in config."
    )


def main():
    parser = argparse.ArgumentParser(description="News Agent Pipeline")
    parser.add_argument(
        "--topic",
        type=str,
        help="Topic to filter news by (overrides config topic.query)",
    )
    args = parser.parse_args()

    config = load_config()
    topic = resolve_topic(config, args.topic)

    pipeline = NewsPipeline()
    pipeline.run(config=config, topic=topic)


if __name__ == "__main__":
    main()