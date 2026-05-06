import streamlit as st
import os
import zipfile
from functools import lru_cache

import google.generativeai as genai
from langchain_community.document_loaders import YoutubeLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# =========================
# 🔐 API KEY
# =========================
def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except:
        return os.getenv("GEMINI_API_KEY")


api_key = get_api_key()

if not api_key:
    st.error("❌ Gemini API key not found. Add it in Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key)


# =========================
# 🤖 GEMINI FUNCTION
# =========================
def generate_content(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


# =========================
# 📥 TRANSCRIPT
# =========================
@lru_cache(maxsize=10)
def extract_transcript(link):
    loader = YoutubeLoader.from_youtube_url(link)
    docs = loader.load()
    return docs[0].page_content


# =========================
# ✂️ SPLIT TEXT
# =========================
def get_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )
    return splitter.split_text(text)


# =========================
# 🔍 CLASSIFIER
# =========================
def is_media_content(text):
    prompt = f"""
Classify content.

Return ONLY:
MEDIA or NON_MEDIA

Content:
{text[:1000]}
"""
    result = generate_content(prompt).upper()
    return "MEDIA" in result


# =========================
# 📝 SUMMARIZATION
# =========================
def summarize_text(text):
    chunks = get_chunks(text)
    summary = ""

    for chunk in chunks:
        prompt = f"""
Convert into a professional article.

Current:
{summary}

New:
{chunk}
"""
        summary = generate_content(prompt)

    return summary


# =========================
# 🌐 WEBPAGE GENERATOR
# =========================
def generate_webpage(article):
    prompt = f"""
Generate HTML, CSS, JS.

--html--
<html>...</html>
--html--

--css--
...
--css--

--js--
...
--js--

Content:
{article}
"""
    return generate_content(prompt)


# =========================
# 🔧 EXTRACT SECTIONS
# =========================
def extract_section(text, tag):
    try:
        return text.split(f"--{tag}--")[1].strip()
    except:
        return ""


# =========================
# 🎯 PROCESS
# =========================
def process_link(link):
    transcript = extract_transcript(link)

    if not is_media_content(transcript):
        return None, "❌ Not media content"

    article = summarize_text(transcript)
    webpage = generate_webpage(article)

    html = extract_section(webpage, "html")
    css = extract_section(webpage, "css")
    js = extract_section(webpage, "js")

    # Save files
    with open("index.html", "w") as f:
        f.write(html)

    with open("style.css", "w") as f:
        f.write(css)

    with open("script.js", "w") as f:
        f.write(js)

    # Zip
    with zipfile.ZipFile("website.zip", "w") as zipf:
        zipf.write("index.html")
        zipf.write("style.css")
        zipf.write("script.js")

    return article, "✅ Success"


# =========================
# 🎨 UI
# =========================
st.set_page_config(page_title="AI Media Generator", layout="centered")

st.title("🎥 AI Media Content Generator")
st.write("Convert YouTube videos into articles + websites")

links_input = st.text_area("Enter YouTube links (comma separated):")

if st.button("🚀 Generate"):

    if not links_input.strip():
        st.warning("Enter at least one link")
    else:
        links = [l.strip() for l in links_input.split(",")]

        with st.spinner("Processing..."):

            for link in links:
                try:
                    st.write(f"🔍 Checking: {link}")

                    article, status = process_link(link)
                    st.write(status)

                    if article:
                        st.success("🎉 Article Generated")

                        st.subheader("📄 Article")
                        st.write(article)

                        with open("website.zip", "rb") as f:
                            st.download_button(
                                "📥 Download Website",
                                data=f,
                                file_name="website.zip"
                            )

                        break

                except Exception as e:
                    st.error(f"Error: {str(e)}")

        st.info("Done")
