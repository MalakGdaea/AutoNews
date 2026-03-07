from newsapi import NewsApiClient
from datetime import datetime, timedelta, timezone
from config import NEWS_API_KEY
from db.models import is_story_used
import feedparser
import re
import time

newsapi = NewsApiClient(api_key=NEWS_API_KEY)

RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "http://rss.cnn.com/rss/edition.rss",
    "https://feeds.reuters.com/reuters/topNews",
]

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

def is_recent(published_str: str, hours: int = 24) -> bool:
    """Check if a story was published within the last X hours."""
    if not published_str:
        return True  # If no date, assume recent
    try:
        # feedparser returns a time.struct_time
        pub_time = datetime(*published_str[:6], tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return pub_time >= cutoff
    except:
        return True

def fetch_newsapi_stories():
    stories = []
    try:
        # Only fetch last 24 hours
        from_date = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
        response = newsapi.get_top_headlines(
            language="en",
            page_size=20
        )
        for article in response.get("articles", []):
            title = article.get("title", "")
            description = article.get("description", "")
            url = article.get("url", "")
            published_at = article.get("publishedAt", "")
            if not title or title == "[Removed]":
                continue
            stories.append({
                "title": title,
                "description": description or "",
                "url": url,
                "published_at": published_at,
                "source": "newsapi",
                "score": score_headline(title)
            })
    except Exception as e:
        print(f"NewsAPI error: {e}")
    return stories

def fetch_rss_stories():
    stories = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                title = entry.get("title", "")
                description = entry.get("summary", "")
                url = entry.get("link", "")
                published = entry.get("published_parsed", None)

                if not title:
                    continue

                # ── STRICT date filter — skip anything older than 24h ──
                if published and not is_recent(published, hours=24):
                    continue

                description = re.sub(r'<[^>]+>', '', description)

                # Format date nicely
                if published:
                    pub_date = datetime(*published[:6]).strftime("%b %d, %Y %H:%M UTC")
                else:
                    pub_date = "Unknown date"

                stories.append({
                    "title": title,
                    "description": description[:300],
                    "url": url,
                    "published_at": pub_date,
                    "source": "rss",
                    "score": score_headline(title)
                })
        except Exception as e:
            print(f"RSS feed error ({feed_url}): {e}")
    return stories

def get_top_stories(limit: int = 5):
    print("📡 Fetching news stories (last 24 hours only)...")

    all_stories = []
    all_stories.extend(fetch_newsapi_stories())
    all_stories.extend(fetch_rss_stories())

    # Remove duplicates
    seen_titles = set()
    unique_stories = []
    for story in all_stories:
        title_key = story["title"][:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_stories.append(story)

    # Filter already used stories
    fresh_stories = [s for s in unique_stories if not is_story_used(s["url"])]

    # Sort by score
    fresh_stories.sort(key=lambda x: x["score"], reverse=True)

    top = fresh_stories[:limit]
    print(f"✅ Found {len(top)} fresh stories from last 24h")
    for s in top:
        print(f"   [{s['score']}pts] {s['published_at']} — {s['title'][:60]}")

    return top