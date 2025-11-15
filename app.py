import streamlit as st
from graph_rag_withneo4j import rag_query, create_knowledge_graph, sample_hotel_reviews
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Hotel Knowledge Graph Chatbot",
    page_icon="🏨",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stTextInput>div>div>input {
        border-radius: 20px;
        padding: 10px 15px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        padding: 10px 24px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
    }
    .chat-message.user {
        background-color: #f0f2f6;
        margin-left: 20%;
    }
    .chat-message.assistant {
        background-color: #e3f2fd;
        margin-right: 20%;
    }
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 1rem;
        flex-shrink: 0;
    }
    .chat-message.user .avatar {
        background-color: #4CAF50;
        color: white;
    }
    .chat-message.assistant .avatar {
        background-color: #2196F3;
        color: white;
    }
    .chat-message .content {
        flex-grow: 1;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your Hotel Knowledge Graph Assistant. You can ask me anything about hotels, their locations, facilities, and reviews. What would you like to know?"}
    ]

# Initialize knowledge graph if not already done
if "knowledge_graph_created" not in st.session_state:
    with st.spinner("Initializing the knowledge graph..."):
        create_knowledge_graph(sample_hotel_reviews)
        st.session_state.knowledge_graph_created = True

# Sidebar with app information
with st.sidebar:
    st.title("🏨 Hotel Knowledge Graph")
    st.markdown("""
    This chatbot helps you explore hotel information using a knowledge graph.
    
    ### Sample Questions:
    - What hotels are located in Dubai?
    - What facilities does Creek Hotel have?
    - Who reviewed the Buckingham Hotel?
    - What types of customers stay at these hotels?
    
    The knowledge graph includes information about:
    - Hotels
    - Locations
    - Facilities
    - Customer Types
    - Reviewers
    """)

# Main chat interface
st.title("Hotel Knowledge Graph Chatbot")
st.markdown("Ask me anything about hotels, their locations, facilities, and reviews!")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about hotels..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Get response from RAG model
        with st.spinner("Searching the knowledge graph..."):
            try:
                response = rag_query(prompt)
                full_response = response
            except Exception as e:
                full_response = f"Sorry, I encountered an error: {str(e)}"
        
        # Display the response
        message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Add a clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your Hotel Knowledge Graph Assistant. You can ask me anything about hotels, their locations, facilities, and reviews. What would you like to know?"}
    ]
    st.rerun()

# Add some space at the bottom
st.markdown("\n\n\n")
st.caption("Powered by Neo4j and OpenAI")
