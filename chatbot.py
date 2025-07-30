import streamlit as st
import pymupdf
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import PyPDF2
import pandas as pd
from datetime import datetime
import pyttsx3
import tempfile

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

def clean_text(text):
    return re.sub(r'\s+', ' ', text.strip().lower())

def extract_text_from_pdf(pdf_file):
    text = ""
    doc = pymupdf.open(stream=pdf_file.read(), filetype="pdf")  
    for page in doc:
        text += page.get_text("text")
    return clean_text(text)

def generate_answers(content, query, tone="Formal"):
    tone_instructions = {
        "Formal": "Please respond in a professional and formal tone.",
        "Friendly": "Please respond in a warm and friendly tone, as if chatting with a friend."
    }

    prompt = f'''
Based on the following content:
{content}

Answer the following question:
{query}

{tone_instructions.get(tone, "")}

Provide a concise and clear answer.
'''
    try:
        response = model.generate_content(prompt)
        return response.candidates[0].content.parts[0].text if response.candidates else "No answer generated."
    except Exception as e:
        return f"Error: {str(e)}"

CHAT_HISTORY_FILE = "chat_history.xlsx"

def log_chat_to_excel(question, answer, tone):
    data = {
        "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Question": [question],
        "Answer": [answer],
        "Tone": [tone]
    }

    new_entry = pd.DataFrame(data)

    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            existing_data = pd.read_excel(CHAT_HISTORY_FILE)
            updated_data = pd.concat([existing_data, new_entry], ignore_index=True)
        else:
            updated_data = new_entry

        updated_data.to_excel(CHAT_HISTORY_FILE, index=False, engine="openpyxl")

    except Exception as e:
        st.error(f"❌ Failed to save chat history: {e}")

# Load PDF and store content in session state
with open('Pakistan2.pdf', 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()
    st.session_state['pdf_content'] = clean_text(full_text)

st.set_page_config(page_title="🔍 Ask PDF: Pakistan Edition", page_icon="📘")
st.title("📘 PDF Question Answering Bot 🤖")
st.markdown("---")

# Personality customization with emojis
tone = st.radio(
    "🎭 Choose chatbot tone:",
    ("Formal 🧐", "Friendly 😊"),
    index=0
)

# Map emoji tones back to plain string for prompt
tone_map = {"Formal 🧐": "Formal", "Friendly 😊": "Friendly"}
selected_tone = tone_map[tone]

user_query = st.text_input("💬 What would you like to know about Pakistan?")

if st.button("🚀 Generate Answer") and st.session_state['pdf_content']:
    content = st.session_state['pdf_content']

    
    # else:
    answer = generate_answers(content, user_query, selected_tone)
    st.subheader("📝 Generated Answer:")
    clean_answer = answer.replace('*', '')
    st.text(clean_answer)
    st.markdown(answer)

    # Text-to-Speech
    engine = pyttsx3.init()
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    engine.save_to_file(answer, temp_audio_file.name)
    engine.runAndWait()
    temp_audio_file.close()

    st.audio(temp_audio_file.name)

    log_chat_to_excel(user_query, answer, selected_tone)

st.markdown("---")
st.subheader("📚 Chat History")
if os.path.exists(CHAT_HISTORY_FILE):
    df = pd.read_excel(CHAT_HISTORY_FILE)
    st.dataframe(df)
else:
    st.info("ℹ️ No chat history yet.")

st.markdown("---")
st.markdown("📌 **Tip:** Use clear and specific questions for the best answers! ✨")
