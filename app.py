import streamlit as st
import os
import json
import tempfile
import vertexai
from vertexai import agent_engines
import uuid
from datetime import datetime
from google.oauth2 import service_account

# === Load credentials from Streamlit Secrets ===
PROJECT_ID = st.secrets["PROJECT_ID"]
LOCATION = st.secrets["LOCATION"] 
STAGING_BUCKET = st.secrets["STAGING_BUCKET"]
RESOURCE_ID = st.secrets["RESOURCE_ID"]

# === Streamlit Page Configuration ===
st.set_page_config(
    page_title="Saarthi - Mental Health Support Bot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Custom CSS Theme ===
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

# === Agent Initialization with Service Account ===
@st.cache_resource
def initialize_agent():
    """Initialize connection to Vertex AI agent with proper authentication."""
    try:
        # Method 1: Try using service account key from secrets
        if "GOOGLE_SERVICE_ACCOUNT_KEY" in st.secrets:
            # Create credentials from service account key
            service_account_info = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT_KEY"])
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            
            # Initialize Vertex AI with explicit credentials
            vertexai.init(
                project=PROJECT_ID,
                location=LOCATION,
                staging_bucket=STAGING_BUCKET,
                credentials=credentials
            )
            
        else:
            # Method 2: Fallback to environment variables (for local development)
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

# === Agent Response Handler ===
def get_agent_response(remote_app, user_id, session_id, message, debug=False):
    try:
        response_text = ""
        for event in remote_app.stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
        ):
            if debug:
                st.write("DEBUG Event:", event.get("author", "unknown"))
            if event.get("author") == "output_agent":
                for part in event.get("content", {}).get("parts", []):
                    if "text" in part:
                        response_text = part["text"].strip()
                        break

        return response_text or "I'm here to listen and support you. Could you tell me more about how you're feeling?"
    except Exception as e:
        return f"I'm experiencing technical difficulties: {str(e)}"

# === Session Creator ===
def create_session(remote_app, user_id):
    try:
        session = remote_app.create_session(user_id=user_id)
        return session["id"], True
    except Exception as e:
        return None, False

# === Session State Defaults ===
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "agent_connected" not in st.session_state:
    st.session_state.agent_connected = False

if "remote_app" not in st.session_state:
    st.session_state.remote_app = None

if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

# === Main App ===
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Saarthi</h1>
        <p>Your AI Mental Health Support Companion</p>
    </div>
    """, unsafe_allow_html=True)

    # Crisis + Disclaimer
    st.markdown("""
    <div class="crisis-box">
        <strong>CRISIS SUPPORT</strong><br>
        If you're in immediate danger: <strong>Call 988 (Suicide & Crisis Lifeline)</strong>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-box">
        <strong>Notice:</strong> This AI bot provides emotional support and general wellness information. 
        It is NOT a replacement for professional mental health care.
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("Control Center")

        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)

        if st.session_state.agent_connected:
            st.success("Connected")
        else:
            st.error("Not connected")

        if st.button("Connect to Saarthi", type="primary"):
            with st.spinner("Connecting..."):
                remote_app, success, msg = initialize_agent()
                if success:
                    st.session_state.remote_app = remote_app
                    st.session_state.agent_connected = True
                    st.success(msg)
                else:
                    st.session_state.agent_connected = False
                    st.error(msg)

        st.divider()
        st.subheader("Session")

        if st.session_state.session_id:
            st.info(f"Active Session: {st.session_state.session_id[:12]}...")
        else:
            st.warning("No active session")

        if st.button("Start New Session"):
            if st.session_state.remote_app:
                session_id, success = create_session(
                    st.session_state.remote_app, st.session_state.user_id
                )
                if success:
                    st.session_state.session_id = session_id
                    st.session_state.messages = []
                    st.success("New session started!")
                    st.rerun()
                else:
                    st.error("Failed to start session")
            else:
                st.error("Please connect first")

        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.success("Chat cleared!")
            st.rerun()

    # Auto-initialize on first load
    if not st.session_state.agent_connected and st.session_state.remote_app is None:
        with st.spinner("Initializing Saarthi..."):
            remote_app, success, message = initialize_agent()
            if success:
                st.session_state.remote_app = remote_app
                st.session_state.agent_connected = True
                
                # Auto-create session
                session_id, sess_success = create_session(remote_app, st.session_state.user_id)
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

    # Main Chat
    if st.session_state.messages:
        st.subheader("Your Safe Space")

        for message in st.session_state.messages:
            role_class = "user-message" if message["role"] == "user" else "bot-message"
            role_label = "You" if message["role"] == "user" else "Saarthi"
            st.markdown(f"""
            <div class="{role_class}">
                {message["content"]}
                <div class="message-time">{role_label} • {message["timestamp"]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Welcome! Your conversation will appear here once you start chatting.")

    st.divider()
    st.markdown("### Share what's on your mind...")

    user_message = st.text_area(
        label="Your message",
        placeholder="Express your thoughts and feelings here... I'm listening with empathy and without judgment.",
        height=120,
        key="user_input",
        label_visibility="collapsed"
    )

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        send_button = st.button("Share", type="primary", use_container_width=True)

    if send_button and user_message.strip():
        if not st.session_state.agent_connected:
            st.error("Please connect to Saarthi first!")
        elif not st.session_state.session_id:
            st.error("No active session. Please start a new session.")
        else:
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

            # Get agent response
            with st.spinner("Saarthi is responding..."):
                response = get_agent_response(
                    st.session_state.remote_app,
                    st.session_state.user_id,
                    st.session_state.session_id,
                    user_message,
                    debug=st.session_state.debug_mode
                )

            # Add agent response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

            st.rerun()

    # Debug info
    if st.session_state.debug_mode:
        st.subheader("Debug Info")
        st.json({
            "connected": st.session_state.agent_connected,
            "session_id": st.session_state.session_id,
            "user_id": st.session_state.user_id,
            "messages_count": len(st.session_state.messages),
            "has_service_account": "GOOGLE_SERVICE_ACCOUNT_KEY" in st.secrets
        })

if __name__ == "__main__":
    main()

