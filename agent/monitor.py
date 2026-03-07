from newsapi import NewsApiClient
from datetime import datetime, timedelta
from config import NEWS_API_KEY
from db.models import is_story_used, mark_story_used
import feedparser
import re

newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# ── RSS feeds to monitor ──────────────────────────
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "http://rss.cnn.com/rss/edition.rss",
    "https://feeds.reuters.com/reuters/topNews",
]

# ── Score a headline for TikTok worthiness ────────
def score_headline(title: str) -> int:
    score = 0
    high_value = [
        "breaking", "urgent", "just in", "massive", "shocking",
        "dead", "killed", "war", "attack", "crisis", "disaster",
        "explosion", "arrested", "convicted", "resigns", "collapses"
    ]
    medium_value = [
        "new", "first", "major", "huge", "record", "biggest",
        "announces", "reveals", "confirms", "warns", "ban"
    ]
    title_lower = title.lower()
    for word in high_value:
        if word in title_lower:
            score += 3
    for word in medium_value:
        if word in title_lower:
            score += 1
    return score

# ── Fetch from NewsAPI ────────────────────────────
def fetch_newsapi_stories():
    stories = []
    try:
        response = newsapi.get_top_headlines(
            language="en",
            page_size=20
        )
        for article in response.get("articles", []):
            title = article.get("title", "")
            description = article.get("description", "")
            url = article.get("url", "")
            if not title or title == "[Removed]":
                continue
            stories.append({
                "title": title,
                "description": description or "",
                "url": url,
                "source": "newsapi",
                "score": score_headline(title)
            })
    except Exception as e:
        print(f"NewsAPI error: {e}")
    return stories

# ── Fetch from RSS feeds ──────────────────────────
def fetch_rss_stories():
    stories = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                description = entry.get("summary", "")
                url = entry.get("link", "")
                if not title:
                    continue
                # Clean HTML tags from description
                description = re.sub(r'<[^>]+>', '', description)
                stories.append({
                    "title": title,
                    "description": description[:300],
                    "url": url,
                    "source": "rss",
                    "score": score_headline(title)
                })
        except Exception as e:
            print(f"RSS feed error ({feed_url}): {e}")
    return stories

# ── Main function — get best stories ─────────────
def get_top_stories(limit: int = 5):
    print("📡 Fetching news stories...")

    all_stories = []
    all_stories.extend(fetch_newsapi_stories())
    all_stories.extend(fetch_rss_stories())

    # Remove duplicates by title similarity
    seen_titles = set()
    unique_stories = []
    for story in all_stories:
        title_key = story["title"][:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_stories.append(story)

    # Filter out already used stories
    fresh_stories = [s for s in unique_stories if not is_story_used(s["url"])]

    # Sort by score
    fresh_stories.sort(key=lambda x: x["score"], reverse=True)

    top = fresh_stories[:limit]
    print(f"✅ Found {len(top)} fresh stories worth covering")
    for s in top:
        print(f"   [{s['score']}pts] {s['title'][:70]}")

    return top