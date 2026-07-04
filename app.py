import os
import streamlit as st
import pandas as pd
import pdfplumber
from supabase import create_client, Client
from dotenv import load_dotenv
from groq import Groq
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Supabase and Groq
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# Streamlit UI
st.title("549-Blood Report Analyzer")

# Show Supabase data (users table)
try:
    response = supabase.table("users").select("*").execute()
    if response.data:
        df = pd.DataFrame(response.data)
        st.subheader("👥 Users Table")
        st.dataframe(df)
    else:
        st.warning("No data found in Supabase table.")
except Exception as e:
    st.error(f"Error fetching data: {e}")

# Sidebar: Past Sessions
st.sidebar.title("📂 Past Sessions")
try:
    sessions = supabase.table("chat_sessions").select("*").execute()
    for s in sessions.data:
        st.sidebar.write(f"Session {s['id']} - {s['created_at']}")
        if st.sidebar.button(f"View {s['id']}"):
            st.write("Report:", s["report_text"])
            st.write("Analysis:", s["analysis"])
except Exception:
    st.sidebar.warning("No past sessions found.")


    # --- Authentication ---
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state["user"] = user.user
            st.success("Logged in successfully!")
        except Exception as e:
            st.error(f"Login failed: {e}")
else:
    st.success(f"Logged in as {st.session_state['user'].email}")

#  PDF Upload & Extraction
uploaded_file = st.file_uploader("Upload Blood Report (PDF)", type=["pdf"])
report_text = ""
session = None

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            report_text += page.extract_text() or ""
    st.subheader("📄 Extracted Report Text")
    st.text_area("Report Content", report_text, height=300)

    #  AI Analysis Agent
    if st.button("Analyze Report"):
        try:
            analysis = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a medical analysis agent. Analyze blood reports."},
                    {"role": "user", "content": report_text}
                ]
            )
            insights = analysis.choices[0].message.content    
            st.subheader("🩺 AI Health Insights")
            st.write(insights)

            # Save session to Supabase
            session = supabase.table("chat_sessions").insert({
                "auth_user_id": st.session_state["user"].id,     
                "report_text": report_text,
                "analysis": insights
            }).execute()
            st.success("✅ Analysis saved to Supabase!")
        except Exception as e:
            st.error(f"Error analyzing report: {e}")

    #Chat Agent (Follow-up Q&A)
    query = st.text_input("Ask a question about your report:")
    if query:
        try:
            splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            docs = splitter.split_text(report_text)
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            db = FAISS.from_texts(docs, embeddings)
            results = db.similarity_search(query, k=3)
            context = " ".join([r.page_content for r in results])

            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a medical chatbot answering based on blood reports."},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
                ]
            )
            reply = completion.choices[0].message.content               
            st.subheader("🤖 Chatbot Answer")
            st.write(reply)

            # Save messages to Supabase
            if session and "id" in session.data[0]:
                supabase.table("chat_messages").insert({
                    "session_id": session.data[0]["id"],
                    "role": "user",
                    "content": query
                }).execute()
                supabase.table("chat_messages").insert({
                    "session_id": session.data[0]["id"],
                    "role": "assistant",
                    "content": reply
                }).execute()
        except Exception as e:
            st.error(f"Error in chatbot: {e}")