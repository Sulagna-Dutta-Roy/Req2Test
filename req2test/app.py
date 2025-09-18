# app.py (UI enhanced)
import streamlit as st
import pandas as pd
import uuid
import datetime
import os
from docx import Document
from openai import OpenAI
import random

# ----------------------------
# OpenAI client
# ----------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------
# Helper functions
# ----------------------------
def extract_requirements(docx_file):
    doc = Document(docx_file)
    requirements = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text and len(text) > 10:
            requirements.append(text)
    return requirements

def generate_mock_test_cases(requirements):
    test_cases = []
    for req in requirements:
        req_id = f"REQ-{str(uuid.uuid4())[:6]}"
        tc_id = f"TC-{str(uuid.uuid4())[:6]}"

        test_cases.append({
            "Requirement ID": req_id,
            "Requirement": req,
            "Test Case ID": tc_id,
            "Title": f"Verify: {req[:40]}...",
            "Preconditions": "System initialized, test user created",
            "Steps": "Step 1: Do X; Step 2: Do Y",
            "Expected Result": "System behaves as per requirement",
            "Compliance": random.choice([
                "IEC 62304 §5.1",
                "21 CFR 11 §11.10",
                "HIPAA §164.312"
            ]),
            "Created At": datetime.datetime.utcnow().isoformat()
        })
    return pd.DataFrame(test_cases)

def generate_ai_test_cases(requirements):
    test_cases = []
    for req in requirements:
        req_id = f"REQ-{str(uuid.uuid4())[:6]}"
        tc_id = f"TC-{str(uuid.uuid4())[:6]}"

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a senior QA engineer for healthcare software. Generate explicit, auditable test cases."},
                    {"role": "user", "content": f"Requirement: {req}\n\nGenerate 1 test case with: Title, Preconditions, Steps, Expected Result, Compliance tags."}
                ],
                temperature=0.3
            )
            content = response.choices[0].message.content

            test_cases.append({
                "Requirement ID": req_id,
                "Requirement": req,
                "Test Case ID": tc_id,
                "Details": content,
                "Created At": datetime.datetime.utcnow().isoformat()
            })
        except Exception as e:
            st.error(f"OpenAI API error: {e}")
            continue
    return pd.DataFrame(test_cases)

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Req2Test-GxP", layout="wide")


# Sidebar controls
st.sidebar.header("⚙️ Settings")
mode = st.sidebar.radio("Generator Mode", ["Mock Generator", "OpenAI Generator"])
st.sidebar.info("💡 Tip: Use *Mock Generator* for offline demo.\nUse *OpenAI Generator* for real AI-powered test cases.")
st.set_page_config(page_title="Req2Test-GxP", page_icon="🧪", layout="wide")

# Custom header
st.markdown(
    """
    <div style="text-align:center; padding: 20px 0;">
        <h1 style="color:#4CAF50;">🧪 Req2Test-GxP</h1>
        <h3 style="color:#FAFAFA;">AI-powered Test Case Generator for Healthcare Compliance</h3>
        <p style="color:gray;">Automating requirement-to-test traceability with GenAI</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Tabs for workflow
tab1, tab2, tab3 = st.tabs(["📂 Upload Requirements", "⚙️ Generate Test Cases", "📊 Review & Export"])

with tab1:
    st.subheader("Upload your Requirements Document")
    uploaded_file = st.file_uploader("Upload a requirements DOCX file", type="docx")
    if uploaded_file:
        requirements = extract_requirements(uploaded_file)
        st.success(f"✅ Extracted {len(requirements)} requirements")
        st.write(requirements)

with tab2:
    if uploaded_file:
        st.subheader("Generate Test Cases")
        if st.button("🚀 Run Generator"):
            with st.status("Generating test cases..."):
                if mode == "Mock Generator":
                    df = generate_mock_test_cases(requirements)
                else:
                    if not client:
                        st.error("⚠️ No OpenAI API key found. Please set OPENAI_API_KEY.")
                        st.stop()
                    df = generate_ai_test_cases(requirements)
            st.session_state["results"] = df
            st.success("✅ Test cases generated successfully!")

with tab3:
    if "results" in st.session_state:
        st.subheader("Review Generated Test Cases")
        df = st.session_state["results"]
        st.dataframe(df, use_container_width=True)

        st.download_button(
            "📥 Download as CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="test_cases.csv",
            mime="text/csv"
        )
        st.download_button(
            "📥 Download as JSON",
            data=df.to_json(orient="records", indent=2).encode("utf-8"),
            file_name="test_cases.json",
            mime="application/json"
        )
    else:
        st.info("⚠️ No test cases yet. Go to 'Generate Test Cases' tab first.")
