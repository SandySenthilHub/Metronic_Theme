import streamlit as st
from uuid import uuid4
import requests
import base64

# Page configuration
st.set_page_config(page_title="Insurance AI App", page_icon="🛡️", layout="wide")

# Custom CSS for better UI
st.markdown(
    """
<style>
    .answer-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .sources-box {
        background-color: #e9ecef;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .report-box {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .report-box table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .report-box th, .report-box td {
        border: 1px solid #dee2e6;
        padding: 0.75rem;
        text-align: left;
    }
    .report-box th {
        background-color: #f1f3f5;
        font-weight: bold;
    }
    .error-box {
        background-color: #fff3f3;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Backend API URL
# BACKEND_URL = "https://a1c882a7b438.ngrok-free.app"
BACKEND_URL = "http://127.0.0.1:8000"


# Initialize session state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"insurance-{uuid4().hex}"
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {}

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select Screen", ["Claim Processing", "Policy Q&A", "Workshop Suggestion"])

# Claim Processing Screen
if page == "Claim Processing":
    st.title("🛡️ Claim Processing")
    st.markdown("Upload required documents for claim analysis.")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Emirates ID", "Driving License", "Vehicle Registry", "Claim Form", "Damaged Photos"])

    with tab1:
        emirates_id = st.file_uploader("Upload Emirates ID (Image/PDF)", type=["jpg", "png", "pdf"])
        if emirates_id:
            st.session_state.uploaded_docs["emirates_id"] = emirates_id

    with tab2:
        driving_license = st.file_uploader("Upload Driving License (Image/PDF)", type=["jpg", "png", "pdf"])
        if driving_license:
            st.session_state.uploaded_docs["driving_license"] = driving_license

    with tab3:
        vehicle_registry = st.file_uploader("Upload Vehicle Registry (Image/PDF)", type=["jpg", "png", "pdf"])
        if vehicle_registry:
            st.session_state.uploaded_docs["vehicle_registry"] = vehicle_registry

    with tab4:
        claim_form = st.file_uploader("Upload Claim Form (Image/PDF)", type=["jpg", "png", "pdf"])
        if claim_form:
            st.session_state.uploaded_docs["claim_form"] = claim_form

    with tab5:
        damaged_photos = st.file_uploader("Upload Damaged Photos (Multiple Images)", type=["jpg", "png"], accept_multiple_files=True)
        if damaged_photos:
            st.session_state.uploaded_docs["damaged_photos"] = damaged_photos

    if st.button("Process Claim", type="primary"):
        if len(st.session_state.uploaded_docs) < 5:
            st.warning("Please upload all required documents.")
        else:
            with st.spinner("Processing documents..."):
                files = []
                for doc_type, file in st.session_state.uploaded_docs.items():
                    if doc_type == "damaged_photos":
                        for photo in file:
                            files.append(("damaged_photos", (photo.name, photo.getvalue(), photo.type)))
                    else:
                        files.append((doc_type, (file.name, file.getvalue(), file.type)))

                try:
                    response = requests.post(f"{BACKEND_URL}/process_claim/", files=files)
                    response.raise_for_status()
                    result = response.json()
                    st.subheader("Raw Backend Response (Debug)")
                    st.json(result)
                    if result.get("status") == "success" and "claims_report" in result:
                        st.subheader("Claims Report")
                        st.markdown('<div class="report-box">', unsafe_allow_html=True)
                        st.markdown(result["claims_report"], unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        if "Unknown" in result["claims_report"] or "Insufficient data" in result["claims_report"]:
                            st.warning("Report contains incomplete data. Check document uploads or backend logs for issues.")
                        else:
                            st.success("Report Generated successfully")
                    else:
                        st.markdown('<div class="error-box">', unsafe_allow_html=True)
                        st.error("No valid claims report received from the backend. Please try again or contact support.")
                        st.json(result)
                        st.markdown('</div>', unsafe_allow_html=True)
                except requests.HTTPError as e:
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.error(f"Backend error processing claim: {str(e)}")
                    if response.text:
                        try:
                            st.json(response.json())
                        except:
                            st.text(response.text)
                    st.markdown('</div>', unsafe_allow_html=True)
                except requests.RequestException as e:
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.error(f"Error connecting to backend: {str(e)}")
                    st.markdown('</div>', unsafe_allow_html=True)

# Policy Q&A Screen
elif page == "Policy Q&A":
    st.title("🛡️ Policy Q&A")
    st.markdown("Ask questions about central government details or insurance policies.")

    question = st.text_area("Ask a question:", placeholder="e.g., What are the terms for motor insurance claims?", height=100)

    if st.button("Get Answer", type="primary"):
        if question.strip():
            try:
                response = requests.post(
                    f"{BACKEND_URL}/policy_qa/",
                    json={"question": question, "thread_id": st.session_state.thread_id}
                )
                response.raise_for_status()
                result = response.json()

                if result["answer"] and result["answer"].strip():
                    st.markdown('<div class="answer-box">', unsafe_allow_html=True)
                    st.subheader("Answer")
                    st.markdown(result["answer"])

                    debug_info = result["debug_info"]
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Confidence", f"{debug_info['answer_confidence']:.1%}")
                    with col2:
                        st.metric("Sources", debug_info["evidence_count"])
                    with col3:
                        st.metric("Iterations", debug_info["iterations"])

                    if debug_info.get("evidence_count", 0) > 0:
                        st.markdown('<div class="sources-box">', unsafe_allow_html=True)
                        st.subheader("Sources")
                        for i, doc in enumerate(debug_info.get("evidence_docs", []), 1):
                            source = doc.get("metadata", {}).get("source", "Unknown")
                            page = doc.get("metadata", {}).get("page", "?")
                            st.write(f"**[{i}]** {source} (page: {page})")
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error("No answer generated.")
            except requests.RequestException as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a question.")

elif page == "Workshop Suggestion":
    st.title("🛡️ Workshop Suggestion")
    st.markdown("Upload 3 workshop summaries for car damage analysis and suggestion.")

    tab1, tab2, tab3 = st.tabs(["Workshop 1", "Workshop 2", "Workshop 3"])

    with tab1:
        workshop1 = st.file_uploader("Upload Workshop 1 Summary (PDF/Image)", type=["pdf", "jpg", "png"])
        if workshop1:
            st.session_state.uploaded_docs["workshop1"] = workshop1

    with tab2:
        workshop2 = st.file_uploader("Upload Workshop 2 Summary (PDF/Image)", type=["pdf", "jpg", "png"])
        if workshop2:
            st.session_state.uploaded_docs["workshop2"] = workshop2

    with tab3:
        workshop3 = st.file_uploader("Upload Workshop 3 Summary (PDF/Image)", type=["pdf", "jpg", "png"])
        if workshop3:
            st.session_state.uploaded_docs["workshop3"] = workshop3

    if st.button("Analyze Workshops", type="primary"):
        required_docs = ["workshop1", "workshop2", "workshop3"]
        if all(doc in st.session_state.uploaded_docs for doc in required_docs):
            with st.spinner("Analyzing workshops..."):
                files = []
                for doc_type in required_docs:
                    file = st.session_state.uploaded_docs[doc_type]
                    files.append((doc_type, (file.name, file.getvalue(), file.type)))

                try:
                    response = requests.post(f"{BACKEND_URL}/workshop_suggestion/", files=files)
                    response.raise_for_status()
                    result = response.json()
                    st.subheader("Raw Backend Response (Debug)")
                    st.json(result)
                    if result.get("status") == "success" and "workshop_report" in result:
                        st.subheader("Workshop Suggestion Report")
                        st.markdown('<div class="report-box">', unsafe_allow_html=True)
                        st.markdown(result["workshop_report"], unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.success("Workshops analyzed successfully!")
                    else:
                        st.markdown('<div class="error-box">', unsafe_allow_html=True)
                        st.error("No valid workshop report received from the backend. Please try again or contact support.")
                        st.json(result)
                        st.markdown('</div>', unsafe_allow_html=True)
                except requests.HTTPError as e:
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.error(f"Backend error analyzing workshops: {str(e)}")
                    if response.text:
                        try:
                            st.json(response.json())
                        except:
                            st.text(response.text)
                    st.markdown('</div>', unsafe_allow_html=True)
                except requests.RequestException as e:
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.error(f"Error connecting to backend: {str(e)}")
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("Please upload all 3 workshop summaries.")

# Footer
st.markdown("---")
st.markdown("🛡️ Insurance AI Application - Built with Streamlit and FastAPI")
