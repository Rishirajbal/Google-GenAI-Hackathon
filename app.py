# app.py - Fixed version
import streamlit as st
import os
import vertexai
from vertexai import agent_engines
import uuid
from datetime import datetime
import time

# Hardcoded credentials - REPLACE THESE WITH YOUR ACTUAL VALUES
PROJECT_ID = st.secrets["PROJECT_ID"]
LOCATION = st.secrets["LOCATION"]
STAGING_BUCKET = st.secrets["STAGING_BUCKET"]
RESOURCE_ID = st.secrets["RESOURCE_ID"]
# Page configuration
st.set_page_config(
    page_title="Saarthi - Mental Health Support Bot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for mental health theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .user-message {
        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 1rem 0;
        margin-left: 15%;
        box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
    }
    
    .bot-message {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        color: #333;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 1rem 0;
        margin-right: 15%;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid #dee2e6;
    }
    
    .message-time {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 0.5rem;
        font-style: italic;
    }
    
    .crisis-box {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
        font-size: 1.1rem;
        box-shadow: 0 6px 20px rgba(220, 53, 69, 0.3);
    }
    
    .disclaimer-box {
        background: linear-gradient(135deg, #ff7b7b 0%, #ff9a9a 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #dc3545;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def initialize_agent():
    """Initialize connection to Vertex AI mental health agent."""
    try:
        # Set environment variables
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
        os.environ["GOOGLE_CLOUD_LOCATION"] = LOCATION
        os.environ["GOOGLE_CLOUD_STAGING_BUCKET"] = STAGING_BUCKET
        
        # Initialize Vertex AI
        vertexai.init(
            project=PROJECT_ID,
            location=LOCATION,
            staging_bucket=STAGING_BUCKET,
        )
        
        # Get the deployed agent
        remote_app = agent_engines.get(RESOURCE_ID)
        return remote_app, True, "Connected to your mental health support bot!"
        
    except Exception as e:
        return None, False, f"Connection failed: {str(e)}"

def get_agent_response(remote_app, user_id, session_id, message):
    """Get response from the mental health agent - FIXED VERSION."""
    try:
        response_text = ""
        response_count = 0
        
        # Debug: Show what we're sending
        st.write(f"DEBUG: Sending message to agent...")
        
        for event in remote_app.stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
        ):
            response_count += 1
            # Debug: Show each event
            st.write(f"DEBUG: Event {response_count}: {event.get('author', 'unknown')}")
            
            # Extract final response from output_agent
            if event.get('author') == 'output_agent':
                if 'content' in event and 'parts' in event['content']:
                    for part in event['content']['parts']:
                        if 'text' in part:
                            response_text = part['text'].strip()
                            st.write(f"DEBUG: Found response: {response_text[:100]}...")
                            break
        
        if not response_text:
            return "I'm here to listen and support you. Could you tell me more about how you're feeling?"
        
        return response_text
        
    except Exception as e:
        st.error(f"Error getting response: {str(e)}")
        return f"I'm experiencing some technical difficulties: {str(e)}"

def create_session(remote_app, user_id):
    """Create a new mental health chat session."""
    try:
        session = remote_app.create_session(user_id=user_id)
        return session['id'], True, "New therapy session started!"
    except Exception as e:
        return None, False, f"Failed to start session: {str(e)}"

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'session_id' not in st.session_state:
    st.session_state.session_id = None

if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if 'agent_connected' not in st.session_state:
    st.session_state.agent_connected = False

if 'remote_app' not in st.session_state:
    st.session_state.remote_app = None

if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Saarthi</h1>
        <p>Your AI Mental Health Support Companion</p>
    </div>
    """, unsafe_allow_html=True)

    # Crisis hotline notice
    st.markdown("""
    <div class="crisis-box">
        <strong>CRISIS SUPPORT</strong><br>
        If you're in immediate danger: <strong>Call 988 (Suicide & Crisis Lifeline)</strong>
    </div>
    """, unsafe_allow_html=True)

    # Important disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        <strong>Important Notice:</strong> This AI bot provides emotional support and general wellness information. 
        It is NOT a replacement for professional mental health care.
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("Control Center")
        
        # Debug mode toggle
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
        
        # Connection status
        if st.session_state.agent_connected:
            st.success("Connected to Saarthi")
        else:
            st.error("Not connected")

        # Initialize/Reconnect button
        if st.button("Connect to Saarthi", type="primary"):
            with st.spinner("Connecting..."):
                remote_app, success, message = initialize_agent()
                if success:
                    st.session_state.remote_app = remote_app
                    st.session_state.agent_connected = True
                    st.success(message)
                else:
                    st.session_state.agent_connected = False
                    st.error(message)

        st.divider()

        # Session management
        st.subheader("Session")
        
        if st.session_state.session_id:
            st.info(f"Active: {st.session_state.session_id[:12]}...")
        else:
            st.warning("No active session")

        if st.button("Start New Session"):
            if st.session_state.remote_app:
                with st.spinner("Starting session..."):
                    session_id, success, message = create_session(
                        st.session_state.remote_app, 
                        st.session_state.user_id
                    )
                    if success:
                        st.session_state.session_id = session_id
                        st.session_state.messages = []
                        st.success("New session started!")
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.error("Please connect first")

        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.success("Chat cleared!")
            st.rerun()

    # Main chat area
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col2:
        # Auto-connect and create session on first load
        if not st.session_state.agent_connected and st.session_state.remote_app is None:
            with st.spinner("Initializing Saarthi..."):
                remote_app, success, message = initialize_agent()
                if success:
                    st.session_state.remote_app = remote_app
                    st.session_state.agent_connected = True
                    
                    # Auto-create session
                    session_id, sess_success, sess_message = create_session(remote_app, st.session_state.user_id)
                    if sess_success:
                        st.session_state.session_id = session_id
                        # Add welcome message
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "Hello! I'm Saarthi, your AI mental health support companion. I'm here to provide a safe, non-judgmental space for you to express your thoughts and feelings. How are you doing today?",
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                    st.rerun()
                else:
                    st.error(f"Failed to initialize: {message}")

        # Chat messages display
        if st.session_state.messages:
            st.subheader("Your Safe Space")
            
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        {message["content"]}
                        <div class="message-time">You • {message["timestamp"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="bot-message">
                        {message["content"]}
                        <div class="message-time">Saarthi • {message["timestamp"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Welcome! Start by connecting to Saarthi and sharing how you're feeling.")

        # Chat input - FIXED VERSION
        st.divider()
        st.markdown("### Share what's on your mind...")
        
        # Fixed text area with proper label
        user_message = st.text_area(
            label="Your message",
            placeholder="Express your thoughts and feelings here... I'm listening with empathy and without judgment.",
            height=120,
            key="user_input",
            label_visibility="collapsed"  # Hide the label but keep it for accessibility
        )
        
        # Send button
        col_send1, col_send2, col_send3 = st.columns([2, 1, 2])
        with col_send2:
            send_button = st.button("Share", type="primary", use_container_width=True)

        # Handle message sending
        if send_button and user_message.strip():
            if not st.session_state.agent_connected:
                st.error("Please connect to Saarthi first!")
            elif not st.session_state.session_id:
                st.error("No active session. Please start a new session.")
            else:
                # Add user message to chat
                st.session_state.messages.append({
                    "role": "user", 
                    "content": user_message,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                # Show loading message
                with st.spinner("Saarthi is processing your message..."):
                    # Get agent response
                    if st.session_state.debug_mode:
                        st.write("DEBUG: Getting response from agent...")
                    
                    response = get_agent_response(
                        st.session_state.remote_app,
                        st.session_state.user_id,
                        st.session_state.session_id,
                        user_message
                    )
                    
                    if st.session_state.debug_mode:
                        st.write(f"DEBUG: Response received: {response}")
                    
                    # Add agent response to chat
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                
                # Clear input and refresh
                st.rerun()

        # Debug info
        if st.session_state.debug_mode:
            st.subheader("Debug Info")
            st.write(f"Connected: {st.session_state.agent_connected}")
            st.write(f"Session ID: {st.session_state.session_id}")
            st.write(f"User ID: {st.session_state.user_id}")
            st.write(f"Messages count: {len(st.session_state.messages)}")

if __name__ == "__main__":
    main()