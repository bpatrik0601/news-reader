import argparse
import yaml

from pipelines.news_pipeline import NewsPipeline


def load_config():
    with open("config/sources.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_topic(config: dict, cli_topic: str | None) -> str:
    if cli_topic:
        print(f"[Main] Using topic from CLI: {cli_topic}")
        return cli_topic

    if "topic" in config and "query" in config["topic"]:
        print(f"[Main] Using topic from config: {config['topic']['query']}")
        return config["topic"]["query"]

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
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Enable step-by-step demo output with explanations",
    )
    args = parser.parse_args()

    config = load_config()
    topic = resolve_topic(config, args.topic)

    pipeline = NewsPipeline(demo=args.demo)
    pipeline.run(config=config, topic=topic)


if __name__ == "__main__":
    main()