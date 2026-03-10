from openai import OpenAI

from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a viral TikTok news script writer.
You write short, punchy, engaging scripts for faceless news TikTok channels.
Your scripts are 60 seconds max when read aloud (around 130-150 words).

CRITICAL FORMATTING RULES for natural, emotional delivery:
- Use "..." for dramatic pauses: "And then... it happened."
- Use CAPS for emphasis on key words: "This is MASSIVE."
- Use short sentences for urgency: "He's gone. Just like that."
- Use questions to create tension: "But why would they do this?"
- Break long thoughts into short punchy lines
- Start with a SHOCKING one liner that creates instant curiosity
- Build tension in the middle
- End with urgency

You NEVER use hashtags or emojis inside the script itself.
You always follow this exact structure:
1. HOOK (0-3 sec): One shocking sentence with CAPS emphasis
2. STORY (3-40 sec): Short punchy sentences, use "..." for pauses
3. REACTION (40-55 sec): Emotional hot take, questions, tension
4. CTA (55-60 sec): "Follow for more breaking news"

Output ONLY the script text. No labels, no stage directions, no formatting.
"""

CAPTION_SYSTEM_PROMPT = """
You write short viral TikTok captions with 5-8 relevant hashtags.
Max 150 characters for the caption itself.

If the headline contains escaped apostrophes like \\' you convert them to normal apostrophes.
If the headline is truncated with "...", rewrite it as one clean complete sentence that preserves the meaning with no ellipsis.

Output ONLY the caption and hashtags, nothing else.
"""


def normalize_headline(title: str) -> str:
    cleaned = (title or "").replace("\\'", "'").strip()
    if cleaned.endswith("..."):
        cleaned = cleaned[:-3].rstrip()
    return " ".join(cleaned.split())


def write_script(title: str, description: str) -> str:
    normalized_title = normalize_headline(title)
    print(f"Writing script for: {normalized_title[:60]}...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Write a TikTok script about this news story:\n\n"
                        f"Title: {normalized_title}\n\n"
                        f"Details: {description}"
                    ),
                },
            ],
            max_tokens=300,
            temperature=0.8,
        )
        script = response.choices[0].message.content.strip()
        print(f"Script written ({len(script.split())} words)")
        return script
    except Exception as error:
        print(f"Script writing error: {error}")
        return None


def write_caption(title: str) -> str:
    print("Writing TikTok caption + hashtags...")
    normalized_title = normalize_headline(title)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": CAPTION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Clean this news headline before writing the caption:\n"
                        "- Remove backslashes before apostrophes.\n"
                        "- If the headline ends with ..., rewrite it as one clean complete sentence with no ellipsis.\n"
                        "- Preserve the meaning.\n\n"
                        f"Headline: {normalized_title}"
                    ),
                },
            ],
            max_tokens=100,
            temperature=0.7,
        )
        caption = response.choices[0].message.content.strip().replace("\\'", "'")
        print("Caption ready")
        return caption
    except Exception as error:
        print(f"Caption error: {error}")
        return normalized_title
