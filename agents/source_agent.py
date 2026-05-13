from datetime import datetime, timedelta
from typing import List, Optional

import feedparser
import requests
import trafilatura

from models.article import Article


class SourceAgent:
    def fetch(
        self,
        sources: List[dict],
        max_per_source: int,
        max_total: int,
        lookback_hours: int,
    ) -> List[Article]:
        articles: List[Article] = []
        cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)

        print(
            f"[SourceAgent] Starting RSS fetch | "
            f"lookback_hours={lookback_hours}, "
            f"max_per_source={max_per_source}, "
            f"max_total={max_total}"
        )

        for source in sources:
            source_count = 0
            feed = feedparser.parse(source["rss"])

            print(
                f"[SourceAgent] Processing source '{source['name']}' | "
                f"RSS entries={len(feed.entries)}"
            )

            for entry in feed.entries:
                if source_count >= max_per_source or len(articles) >= max_total:
                    break

                published_at = self._parse_published_date(entry)
                if published_at and published_at < cutoff:
                    continue

                clean_text = self._extract_clean_text(entry.link)
                if not clean_text:
                    continue

                articles.append(
                    Article(
                        source=source["name"],
                        title=entry.title,
                        url=entry.link,
                        published_at=published_at.isoformat() if published_at else None,
                        content=clean_text,
                    )
                )

                source_count += 1

            print(
                f"[SourceAgent] Source '{source['name']}' fetched articles={source_count}"
            )

            if len(articles) >= max_total:
                print(
                    f"[SourceAgent] Global article limit reached ({max_total}), stopping fetch"
                )
                break

        # Final aggregation
        per_source_stats = {}
        for article in articles:
            per_source_stats[article.source] = (
                per_source_stats.get(article.source, 0) + 1
            )

        print(f"[SourceAgent] Fetch completed | total_articles={len(articles)}")
        for source, count in per_source_stats.items():
            print(
                f"[SourceAgent] Final count | source='{source}' articles={count}"
            )

        return articles

    def _parse_published_date(self, entry) -> Optional[datetime]:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                return datetime(*entry.published_parsed[:6])
            except Exception:
                return None
        return None

    def _extract_clean_text(self, url: str) -> str:
        """
        Download article HTML and extract clean main text using trafilatura.
        """
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return ""

            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
            )

            if not text:
                return ""

            return self._normalize_text(text)

        except Exception:
            return ""
        

    def _normalize_text(self, text: str, max_chars: int = 8_000) -> str:
        """
        Normalize whitespace and limit text length for LLM usage.
        """
        normalized = " ".join(text.split())

        if len(normalized) > max_chars:
            normalized = normalized[:max_chars]

        return normalized