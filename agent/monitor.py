from datetime import datetime, timedelta, timezone
import re

import feedparser
from newsapi import NewsApiClient

from config import NEWS_API_KEY
from db.models import get_topic_config, is_story_used

newsapi = NewsApiClient(api_key=NEWS_API_KEY)

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "http://rss.cnn.com/rss/edition.rss",
    "https://feeds.reuters.com/reuters/topNews",
]

PRIMARY_CONFLICT_TERMS = []
SECONDARY_CONFLICT_TERMS = []
RELEVANCE_THRESHOLD = 5


def _load_topic_config() -> None:
    global PRIMARY_CONFLICT_TERMS, SECONDARY_CONFLICT_TERMS, RELEVANCE_THRESHOLD
    config = get_topic_config()
    PRIMARY_CONFLICT_TERMS = config.get("primary_terms", [])
    SECONDARY_CONFLICT_TERMS = config.get("secondary_terms", [])
    RELEVANCE_THRESHOLD = int(config.get("relevance_threshold", 5))


def score_headline(title: str) -> int:
    score = 0
    high_value = [
        "breaking",
        "urgent",
        "just in",
        "massive",
        "shocking",
        "dead",
        "killed",
        "war",
        "attack",
        "crisis",
        "disaster",
        "explosion",
        "arrested",
        "convicted",
        "resigns",
        "collapses",
    ]
    medium_value = [
        "new",
        "first",
        "major",
        "huge",
        "record",
        "biggest",
        "announces",
        "reveals",
        "confirms",
        "warns",
        "ban",
    ]

    title_lower = title.lower()
    for word in high_value:
        if word in title_lower:
            score += 3
    for word in medium_value:
        if word in title_lower:
            score += 1
    return score


def score_conflict_relevance(title: str, description: str = "") -> int:
    text = f"{title} {description}".lower()
    score = 0

    primary_hits = sum(1 for term in PRIMARY_CONFLICT_TERMS if term in text)
    secondary_hits = sum(1 for term in SECONDARY_CONFLICT_TERMS if term in text)

    score += primary_hits * 4
    score += secondary_hits * 2

    if primary_hits >= 2:
        score += 4
    if primary_hits >= 1 and secondary_hits >= 1:
        score += 3

    return score


def is_conflict_relevant(story: dict) -> bool:
    relevance = score_conflict_relevance(story.get("title", ""), story.get("description", ""))
    return relevance >= RELEVANCE_THRESHOLD


def is_recent(published_str: str, hours: int = 24) -> bool:
    if not published_str:
        return True
    try:
        pub_time = datetime(*published_str[:6], tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return pub_time >= cutoff
    except Exception:
        return True


def fetch_newsapi_stories():
    stories = []
    try:
        response = newsapi.get_top_headlines(language="en", page_size=30)
        for article in response.get("articles", []):
            title = article.get("title", "")
            description = article.get("description", "")
            url = article.get("url", "")
            published_at = article.get("publishedAt", "")
            if not title or title == "[Removed]":
                continue

            stories.append(
                {
                    "title": title,
                    "description": description or "",
                    "url": url,
                    "published_at": published_at,
                    "image_url": article.get("urlToImage", None),
                    "source": "newsapi",
                    "headline_score": score_headline(title),
                    "relevance_score": score_conflict_relevance(title, description or ""),
                }
            )
    except Exception as exc:
        print(f"NewsAPI error: {exc}")
    return stories


def fetch_rss_stories():
    stories = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                description = entry.get("summary", "")
                url = entry.get("link", "")
                published = entry.get("published_parsed", None)

                if not title:
                    continue
                if published and not is_recent(published, hours=24):
                    continue

                description = re.sub(r"<[^>]+>", "", description)
                clean_description = description[:300]

                if published:
                    pub_date = datetime(*published[:6]).strftime("%b %d, %Y %H:%M UTC")
                else:
                    pub_date = "Unknown date"

                stories.append(
                    {
                        "title": title,
                        "description": clean_description,
                        "url": url,
                        "published_at": pub_date,
                        "source": "rss",
                        "headline_score": score_headline(title),
                        "relevance_score": score_conflict_relevance(title, clean_description),
                    }
                )
        except Exception as exc:
            print(f"RSS feed error ({feed_url}): {exc}")
    return stories


def get_top_stories(limit: int = 5):
    _load_topic_config()
    print("Fetching news stories (last 24 hours only)...")
    print(
        f"Topic targeting loaded: {len(PRIMARY_CONFLICT_TERMS)} primary, "
        f"{len(SECONDARY_CONFLICT_TERMS)} secondary, threshold={RELEVANCE_THRESHOLD}"
    )

    all_stories = []
    all_stories.extend(fetch_newsapi_stories())
    all_stories.extend(fetch_rss_stories())

    seen_titles = set()
    unique_stories = []
    for story in all_stories:
        title_key = story["title"][:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_stories.append(story)

    fresh_stories = [s for s in unique_stories if not is_story_used(s["url"])]
    relevant = [s for s in fresh_stories if is_conflict_relevant(s)]

    def combined_score(story: dict) -> int:
        return int(story.get("relevance_score", 0)) * 3 + int(story.get("headline_score", 0))

    relevant.sort(key=combined_score, reverse=True)

    selected_pool = relevant
    if not selected_pool:
        print("No conflict-specific stories found. Falling back to general breaking stories.")
        selected_pool = fresh_stories
        selected_pool.sort(key=lambda x: x.get("headline_score", 0), reverse=True)

    top = selected_pool[:limit]
    print(f"Found {len(top)} stories")
    for story in top:
        print(
            f"   [rel={story.get('relevance_score', 0)} | head={story.get('headline_score', 0)}] "
            f"{story['published_at']} - {story['title'][:80]}"
        )

    return top
