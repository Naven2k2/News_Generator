import os
import zipfile
from dotenv import load_dotenv
from functools import lru_cache

from google import genai
from langchain_community.document_loaders import YoutubeLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# =========================
# LOAD ENV + GEMINI
# =========================
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# =========================
# GEMINI FUNCTION
# =========================
def generate_content(prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    return response.text


# =========================
# TRANSCRIPT EXTRACTION
# =========================
@lru_cache(maxsize=10)
def extract_transcript(link):
    loader = YoutubeLoader.from_youtube_url(link)
    docs = loader.load()
    return docs[0].page_content


# =========================
# TEXT SPLITTING
# =========================
def get_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=200
    )
    return splitter.split_text(text)


# =========================
# 🔥 MEDIA CONTENT CLASSIFIER
# =========================
def is_media_content(text):
    prompt = f"""
Classify this content.

Return ONLY:
MEDIA → if related to AI, tech, news, YouTube, digital content, marketing
NON_MEDIA → otherwise

Content:
{text[:1000]}
"""
    result = generate_content(prompt).strip().upper()
    return "MEDIA" in result


# =========================
# FILTER LINKS
# =========================
def filter_media_links(links):
    valid_links = []

    for link in links:
        try:
            print(f"🔍 Checking: {link}")
            text = extract_transcript(link)

            if is_media_content(text):
                print("✅ Media content detected")
                valid_links.append(link)
            else:
                print("❌ Not media content")

        except Exception as e:
            print(f"⚠ Skipped: {link}")

    return valid_links


# =========================
# BASE SUMMARIZER
# =========================
def base_summarizer(link):
    transcript = extract_transcript(link)

    prompt = f"""
Convert this YouTube transcript into a professional article.

Rules:
- Remove ads/promotions
- Use headings, bullet points
- Keep it clean and structured

Transcript:
{transcript}
"""
    return generate_content(prompt)


# =========================
# RECURSIVE SUMMARIZER
# =========================
def recursive_summarize(text):
    chunks = get_chunks(text)
    summary = ""

    for chunk in chunks:
        prompt = f"""
Current Summary:
{summary}

New Content:
{chunk}

Update article professionally.
"""
        summary = generate_content(prompt)

    return summary


def long_summarizer(link):
    text = extract_transcript(link)
    return recursive_summarize(text)


# =========================
# LENGTH CHECK
# =========================
def is_long(link):
    return len(extract_transcript(link)) > 1000


# =========================
# WEBPAGE GENERATOR
# =========================
def generate_webpage(article):
    prompt = f"""
You are a frontend developer.

Generate output strictly in format:

--html--
<html>...</html>
--html--

--css--
...
--css--

--js--
...
--js--

Create webpage for:
{article}
"""
    return generate_content(prompt)


# =========================
# SMART PIPELINE
# =========================
def smart_pipeline(link):
    if is_long(link):
        article = long_summarizer(link)
    else:
        article = base_summarizer(link)

    return generate_webpage(article)


# =========================
# EXTRACT HTML/CSS/JS
# =========================
def extract_section(text, tag):
    try:
        return text.split(f"--{tag}--")[1].strip()
    except:
        return ""


# =========================
# MAIN FUNCTION
# =========================
def main():
    links_input = input("Enter YouTube URLs (comma separated): ")
    links = [l.strip() for l in links_input.split(",")]

    print("\n🔍 Filtering media content...\n")

    media_links = filter_media_links(links)

    if not media_links:
        print("❌ No media-related links found")
        return

    selected_link = media_links[0]
    print(f"\n🎯 Selected Link: {selected_link}")

    try:
        print("⏳ Processing...")

        result = smart_pipeline(selected_link)

        html = extract_section(result, "html")
        css = extract_section(result, "css")
        js = extract_section(result, "js")

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)

        with open("style.css", "w", encoding="utf-8") as f:
            f.write(css)

        with open("script.js", "w", encoding="utf-8") as f:
            f.write(js)

        with zipfile.ZipFile("website.zip", "w") as zipf:
            zipf.write("index.html")
            zipf.write("style.css")
            zipf.write("script.js")

        print("\n✅ Website generated successfully!")
        print("📦 Output: website.zip")

    except Exception as e:
        print("❌ Error:", str(e))


# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()