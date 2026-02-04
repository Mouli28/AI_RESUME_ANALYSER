import streamlit as st
import pdfplumber
import requests

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
    # Trigger Screening
    # --------------------------------------------------
    if st.button("Analyze Resume & Send Email"):
        # Validation
        if not all([resume_text, job_description, recipient_email]):
            st.error("❌ Resume, Job Description, and Email are mandatory.")
            st.stop()

        payload = {
            "resume_text": resume_text,
            "job_description": job_description,
            "recipient_email": recipient_email
        }

        with st.spinner("🔍 Screening resume using AI..."):
            try:
                response = requests.post(
                    N8N_WEBHOOK_URL,
                    json=payload,
                    timeout=30
                )

                if response.status_code != 200:
                    st.error("❌ Workflow failed. Please try again.")
                    st.text(response.text)
                    st.stop()

                result = response.json()

                # --------------------------------------------------
                # UI Feedback Based on n8n Response
                # --------------------------------------------------
                if result.get("status") == "SELECTED":
                    st.success("🎉 Candidate is suitable! Selection email sent successfully.")

                elif result.get("status") == "REJECTED":
                    st.warning("📩 Candidate is not suitable. Rejection email sent.")

                else:
                    st.info("ℹ️ Resume processed.")

            except Exception as e:
                st.error("❌ Failed to connect to the automation workflow.")
                st.exception(e)
