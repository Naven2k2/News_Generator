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
    st.error("❌ Gemini API key not found.")
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
# 📥 TRANSCRIPT (SAFE)
# =========================
@lru_cache(maxsize=10)
def extract_transcript(link):
    try:
        loader = YoutubeLoader.from_youtube_url(link)
        docs = loader.load()
        return docs[0].page_content
    except:
        return None


# =========================
# ✂️ TEXT SPLITTING
# =========================
def get_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )
    return splitter.split_text(text)


# =========================
# 📝 SUMMARIZATION
# =========================
def summarize_text(text):
    chunks = get_chunks(text)
    summary = ""

    for chunk in chunks:
        prompt = f"""
Convert into a professional article with headings and bullet points.

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
Generate a clean webpage.

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
# 🔧 EXTRACT HTML/CSS/JS
# =========================
def extract_section(text, tag):
    try:
        return text.split(f"--{tag}--")[1].strip()
    except:
        return ""


# =========================
# 🎯 PROCESS
# =========================
def process(link, manual_text):
    transcript = extract_transcript(link)

    # 🚨 Fallback logic (IMPORTANT FIX)
    if not transcript:
        if manual_text:
            st.warning("⚠️ Using manually provided transcript")
            transcript = manual_text
        else:
            return None, "❌ Transcript not available. Paste manually."

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

    # Create ZIP
    with zipfile.ZipFile("website.zip", "w") as zipf:
        zipf.write("index.html")
        zipf.write("style.css")
        zipf.write("script.js")

    return article, "✅ Success"


# =========================
# 🎨 STREAMLIT UI
# =========================
st.set_page_config(page_title="AI Media Generator", layout="centered")

st.title("🎥 AI Media Content Generator")
st.write("Convert YouTube videos into articles + websites")

links_input = st.text_area("Enter YouTube links (comma separated):")

# 🔥 NEW FEATURE
manual_text = st.text_area("Or paste transcript manually (if YouTube fails):")

if st.button("🚀 Generate"):

    if not links_input.strip() and not manual_text.strip():
        st.warning("Please enter a link or paste transcript")
    else:
        links = [l.strip() for l in links_input.split(",") if l.strip()]

        with st.spinner("Processing..."):

            if links:
                for link in links:
                    try:
                        st.write(f"🔍 Checking: {link}")

                        article, status = process(link, manual_text)
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
                        st.error(f"❌ Error: {str(e)}")

            else:
                # If only manual input
                article = summarize_text(manual_text)
                webpage = generate_webpage(article)

                html = extract_section(webpage, "html")
                css = extract_section(webpage, "css")
                js = extract_section(webpage, "js")

                with open("index.html", "w") as f:
                    f.write(html)

                with open("style.css", "w") as f:
                    f.write(css)

                with open("script.js", "w") as f:
                    f.write(js)

                with zipfile.ZipFile("website.zip", "w") as zipf:
                    zipf.write("index.html")
                    zipf.write("style.css")
                    zipf.write("script.js")

                st.success("🎉 Generated from manual transcript")

                st.subheader("📄 Article")
                st.write(article)

                with open("website.zip", "rb") as f:
                    st.download_button(
                        "📥 Download Website",
                        data=f,
                        file_name="website.zip"
                    )

        st.info("✅ Done")
