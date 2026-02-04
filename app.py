import streamlit as st
import pdfplumber
import requests
import google.generativeai as genai

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="AI Document Orchestrator",
    layout="centered"
)

st.title("📄 AI-Powered Document Orchestrator")

st.markdown(
    "Upload a document, ask questions using AI, and trigger automated workflows."
)

# --------------------------------------------------
# Secrets
# --------------------------------------------------
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# --------------------------------------------------
# Document Upload
# --------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload Resume / Document (PDF only) *",
    type=["pdf"]
)

document_text = ""

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
        document_text = "\n".join(pages)

    st.subheader("📑 Extracted Document Text")
    st.text_area("", document_text, height=250)

# --------------------------------------------------
# Query Section (AI Answering ONLY)
# --------------------------------------------------
st.subheader("🔎 Ask a question about this document")

user_question = st.text_input(
    "Enter your question",
    placeholder="e.g. What is the candidate's contact information?"
)

# -------------------------------
# Answer Query Button
# -------------------------------
if st.button("Answer Query"):

    if not uploaded_file or not document_text:
        st.error("❌ Please upload a document first.")
        st.stop()

    if not user_question:
        st.error("❌ Please enter a question.")
        st.stop()

    with st.spinner("🤖 Answering your question..."):
        question_prompt = f"""
You are an AI document analyst.

Document:
{document_text}

User Question:
{user_question}

Instructions:
- Answer strictly using the document content.
- Extract only what is required.
- If not present, say:
  "Information not available in the document."
- Be concise and professional.
"""

        ai_response = model.generate_content(question_prompt)
        answer = ai_response.text.strip()

    st.subheader("🧠 AI Answer")
    st.write(answer)

# --------------------------------------------------
# Automation Inputs (AFTER QUERY)
# --------------------------------------------------
st.subheader("⚙️ Automation Details")

recipient_email = st.text_input(
    "Recipient Email *",
    placeholder="example@email.com"
)

job_description = st.text_area(
    "Job Description (JD) *",
    height=180,
    placeholder="Paste the job description here"
)

# --------------------------------------------------
# Analyze & Trigger Automation
# --------------------------------------------------
if st.button("Analyze & Trigger Automation"):

    if not uploaded_file or not document_text:
        st.error("❌ Document is required.")
        st.stop()

    if not recipient_email or not job_description:
        st.error("❌ Email and Job Description are mandatory.")
        st.stop()

    # ✅ FINAL PAYLOAD (ONLY WHAT YOU WANT)
    payload = {
        "resume_text": document_text,
        "job_description": job_description,
        "recipient_email": recipient_email
    }

    with st.spinner("🔍 Screening resume and sending email..."):
        try:
            response = requests.post(
                N8N_WEBHOOK_URL,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                st.error("❌ Workflow failed.")
                st.text(response.text)
                st.stop()

            result = response.json()

            # -------------------------------
            # UI Feedback
            # -------------------------------
            if result.get("status") == "SELECTED":
                st.success("🎉 Candidate is suitable! Selection email sent.")

            elif result.get("status") == "REJECTED":
                st.warning("📩 Candidate not suitable. Rejection email sent.")

            else:
                st.info("ℹ️ Resume processed.")

        except Exception as e:
            st.error("❌ Failed to connect to automation workflow.")
            st.exception(e)
