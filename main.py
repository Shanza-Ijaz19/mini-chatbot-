import streamlit as st
from azure.ai.language.questionanswering import QuestionAnsweringClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.language.questionanswering import models as qna
import os
from dotenv import load_dotenv
load_dotenv() #load if env exist
#getting azure key and endpoint
end_point=os.getenv("AZURE_ENDPOINT")
api_key=os.getenv("AZURE_KEY")
project_name=os.getenv("PROJECT_NAME")
if not end_point or not api_key:
    st.error(
        "Endpoint ya Key nahi mili. `.env` file check karein. "
        "Set LANGUAGE_ENDPOINT & LANGUAGE_KEY (ya AZURE_QUESTIONANSWERING_... variants)."
    )
    st.stop()
st.set_page_config(page_title="Azure CQA - Streamlit", layout="centered")

st.title("mini ilets chatbot demo by Shanza 🙂")
st.markdown(
    "Apna sawaal type karein aur jawab hasil karein. "
    "Shukria😊"
)
# --- 2) UI: allow selecting deployment (test or production)
st.sidebar.header("Settings")
deployment = st.sidebar.selectbox("Deployment name", ["test", "production"])
# optional: let user override project name if env var missing
if not project_name:
    project_name = st.sidebar.text_input("Project name (required if not in .env)", "")

if not project_name:
    st.warning("Project name set karein (sidebar se).")
    # we won't stop here because user may want to query with inline text option; but for project queries it's needed.
# Question input area
question = st.text_area("Ask Your Question:", height=120)
top_k = st.slider("Max answers to return (top k)", min_value=1, max_value=5, value=3)

# Optional: confidence threshold slider (0-1)
confidence_threshold = st.slider("Minimum confidence threshold (0 to 1)", 0.0, 1.0, 0.2, 0.01)

# Button to send the request
if st.button("Get answer from Azure CQA"):
    if not question.strip():
        st.warning("Please type a question first.")
    else:
        # Create client
        try:
            client = QuestionAnsweringClient(end_point, AzureKeyCredential(api_key))
        except Exception as e:
            st.error(f"Client creation failed: {e}")
            raise

        with st.spinner("Azure se jawab le rahe hain..."):
            try:
                # Use the get_answers method to query the deployed project
                # We pass project_name and deployment_name as keyword-only args (as per SDK)
                response = client.get_answers(
                    question=question,
                    top=top_k,
                    confidence_threshold=confidence_threshold,
                    include_unstructured_sources=True,   # agar aapke sources mein unstructured docs hain to fayda
                    project_name=project_name,
                    deployment_name=deployment
                )
            except Exception as e:
                st.error(f"Request failed: {e}")
                st.stop()
        # Response object -> response.answers (list)
        answers = getattr(response, "answers", None)
        if not answers:
            st.info("Koi jawab nahi mila (answers list empty).")
        else:
            st.subheader("Answers")
            # Sort / show answers with confidence & source info
            for idx, ans in enumerate(answers, start=1):
                # each ans has .answer, .confidence, .source, .id, .metadata, .questions (alternate phrasings)
                st.markdown(f"**{idx}. Answer (confidence: {ans.confidence:.2f})**")
                st.write(ans.answer)
                # show additional info in an expander
                with st.expander("Answer details"):
                    st.write("**Source:**", getattr(ans, "source", "N/A"))
                    st.write("**QnA id:**", getattr(ans, "id", "N/A"))
                    st.write("**Matched questions (if any):**", getattr(ans, "questions", []))
                    st.write("**Metadata:**", getattr(ans, "metadata", {}))
                    # If the SDK returned dialog/prompts or short answers, show them
                    if getattr(ans, "dialog", None):
                        st.write("**Dialog info:**", ans.dialog)
         # Close client (good practice)
        client.close()
# Footer / notes
st.markdown("---")
st.caption(
    "Note: Use API keys securely. For production consider Managed Identities or Azure Key Vault. "
    "This demo uses API key from environment variables for simplicity."
)