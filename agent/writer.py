from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a viral TikTok news script writer. 
You write short, punchy, engaging scripts for faceless news TikTok channels.
Your scripts are 60 seconds max when read aloud (around 130-150 words).
You write in a dramatic, engaging tone that keeps viewers watching.
You NEVER use hashtags or emojis inside the script itself.
You always follow this exact structure:
1. HOOK (0-3 sec): One shocking sentence to stop the scroll
2. STORY (3-40 sec): The news explained simply and fast
3. REACTION (40-55 sec): A hot take or emotional angle
4. CTA (55-60 sec): "Follow for more breaking news"
Output ONLY the script text. No labels, no stage directions, no formatting.
"""

def write_script(title: str, description: str) -> str:
    print(f"✍️  Writing script for: {title[:60]}...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Write a TikTok script about this news story:\n\nTitle: {title}\n\nDetails: {description}"}
            ],
            max_tokens=300,
            temperature=0.8
        )
        script = response.choices[0].message.content.strip()
        print(f"✅ Script written ({len(script.split())} words)")
        return script
    except Exception as e:
        print(f"❌ Script writing error: {e}")
        return None

def write_caption(title: str) -> str:
    print("📝 Writing TikTok caption + hashtags...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You write short viral TikTok captions with 5-8 relevant hashtags. Max 150 characters for the caption. Output ONLY the caption and hashtags, nothing else."},
                {"role": "user", "content": f"Write a TikTok caption for this news: {title}"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        caption = response.choices[0].message.content.strip()
        print(f"✅ Caption ready")
        return caption
    except Exception as e:
        print(f"❌ Caption error: {e}")
        return title