import os
import streamlit as st
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set page config
st.set_page_config(page_title="Condominium Rules Chatbot", page_icon="🏠")

# Initialize session state for messages if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to process uploaded files
def process_uploaded_files(uploaded_files):
    combined_text = ""
    for uploaded_file in uploaded_files:
        if uploaded_file.type == "application/pdf":
            combined_text += extract_text_from_pdf(uploaded_file) + "\n\n"
        elif uploaded_file.type == "text/plain":
            combined_text += uploaded_file.getvalue().decode("utf-8") + "\n\n"
    return combined_text

# Sidebar for file uploads
with st.sidebar:
    st.title("🏠 Condo Rules Setup")
    st.markdown("Upload your condominium rules documents")
    
    uploaded_files = st.file_uploader(
        "Upload PDF or TXT files with your condominium rules",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.session_state.condo_rules = process_uploaded_files(uploaded_files)
        st.success("Files uploaded successfully!")
    elif "condo_rules" not in st.session_state:
        st.session_state.condo_rules = ""
    
    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Upload your condo rules documents (PDF/TXT)")
    st.markdown("2. Chat with the assistant in the main window")
    st.markdown("3. Ask questions about your condo rules")

# Main chat interface
st.title("🏠 Condominium Rules Chatbot")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about the condominium rules..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Prepare the context for OpenAI
    context = f"""
    You are a helpful assistant that answers questions about condominium rules and regulations.
    Below is the relevant information from the condominium documents:
    
    {st.session_state.condo_rules}
    
    Current conversation:
    """
    
    # Include previous messages for context
    for msg in st.session_state.messages[-6:]:  # Keep last 6 messages for context
        context += f"\n{msg['role']}: {msg['content']}"
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Call OpenAI API
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions about condominium rules and regulations. Use the provided documents to answer questions accurately. If you don't know the answer, say so."},
                    {"role": "user", "content": context + "\nassistant: "}
                ],
                stream=True,
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
