import argparse
import yaml

import config
from pipelines.news_pipeline import NewsPipeline


def load_config():
    with open("config/sources.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_topic(config: dict, cli_topic: str | None, interactive: bool) -> str: 
# 1) Interactive: teljes felülírás (nem keverjük a YAML-lal)
    if interactive:
        user_input = input("Adj meg kulcsszavakat vesszővel elválasztva: ")
        topics = [k.strip() for k in user_input.split(",") if k.strip()]
        if not topics:
            raise RuntimeError("Nem adtál meg kulcsszót interactive módban.")
        print(f"[Main] Using interactive keywords: {topics}")
        return topics

    # 2) CLI --topic: felülírja a configot
    if cli_topic:
        print(f"[Main] Using topic from CLI: {cli_topic}")
        return cli_topic

    # 3) Config: queries (lista) vagy query (string)
    topic_cfg = config.get("topic", {})
    if "queries" in topic_cfg and topic_cfg["queries"]:
        print(f"[Main] Using topics from config: {topic_cfg['queries']}")
        return topic_cfg["queries"]

    if "query" in topic_cfg and topic_cfg["query"]:
        print(f"[Main] Using topic from config: {topic_cfg['query']}")
        return topic_cfg["query"]

    raise RuntimeError("No topic specified. Use --topic, --interactive or define topic.query / topic.queries in config.")



def main():
    parser = argparse.ArgumentParser(description="News Agent Pipeline")
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Topic to filter news by (overrides config topic.query)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Enable step-by-step demo output with explanations",
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=[1, 2, 3],
        default=2,
        help="Control demo complexity: 1=simple, 2=with clustering, 3=full pipeline",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start the pipeline in interactive mode",
    )

    args = parser.parse_args()

    # CONFIG BETÖLTÉSE ELŐSZÖR (hogy a topicot is meg tudjuk határozni)
    config = load_config()
    
    # TOPIC RESOLVE (ez kezel mindent)
    topic = resolve_topic(config, args.topic, args.interactive)

    # PIPELINE INDÍTÁSA
    pipeline = NewsPipeline(demo=args.demo, level=args.level)
    pipeline.run(config=config, topic=topic)


if __name__ == "__main__":
    main()