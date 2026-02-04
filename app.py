import streamlit as st
import pdfplumber
import requests
import json
import google.generativeai as genai

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="AI Resume Analyzer",
    layout="centered"
)

st.title("📄 AI Resume Analyzer & Automated Email System")

# --------------------------------------------------
# Secrets
# --------------------------------------------------
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# --------------------------------------------------
# Resume Upload
# --------------------------------------------------
uploaded_file = st.file_uploader(
    "Upload Resume (PDF only) *",
    type=["pdf"]
)

resume_text = ""

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
        resume_text = "\n".join(pages)

    st.subheader("📑 Extracted Resume Text")
    st.text_area("", resume_text, height=220)

# --------------------------------------------------
# Mandatory Inputs
# --------------------------------------------------
st.subheader("🧾 Job Details (All Mandatory)")

job_description = st.text_area(
    "Job Description (JD) *",
    height=180,
    placeholder="Paste the full job description here"
)

recipient_email = st.text_input(
    "Candidate / Recruiter Email *",
    placeholder="example@email.com"
)

# --------------------------------------------------
# Trigger Screening (ALL LOGIC HERE)
# --------------------------------------------------
if st.button("Analyze Resume & Send Email"):

    if not uploaded_file or not resume_text or not job_description or not recipient_email:
        st.error("❌ Resume, Job Description, and Email are mandatory.")
        st.stop()

    # -------------------------------
    # STEP 1 — Resume → Structured JSON
    # -------------------------------
    with st.spinner("🧠 Extracting structured resume data..."):

        resume_prompt = f"""
You are an expert resume parser.

Extract the most important information from the resume below.

Resume Text:
{resume_text}

Return ONLY valid JSON in the following format:
{{
  "name": "",
  "email": "",
  "phone": "",
  "current_role": "",
  "total_experience": "",
  "skills": [],
  "education": [],
  "projects": [],
  "summary": ""
}}

Rules:
- No markdown
- No explanations
- Return pure JSON only
"""

        response = model.generate_content(resume_prompt)
        raw_output = response.text.strip()

        try:
            resume_json = json.loads(raw_output)
        except json.JSONDecodeError:
            st.error("❌ Failed to extract structured resume data.")
            st.text(raw_output)
            st.stop()

    st.subheader("📄 Structured Resume (JSON)")
    st.json(resume_json)

    # -------------------------------
    # STEP 2 — Send to n8n
    # -------------------------------
    payload = {
        "resume_text": resume_text,
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
