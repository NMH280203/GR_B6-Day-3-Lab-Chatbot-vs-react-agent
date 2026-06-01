import os
import sys
import time
import streamlit as st

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.provider_factory import get_provider
from src.tools.hr_tools import TOOLS_METADATA
from src.agent.chatbot import HRBaselineChatbot
from src.agent.agent import ReActAgent
from src.telemetry.metrics import tracker

# 1. Page Configuration & Premium styling
st.set_page_config(
    page_title="HR Agentic Workspace",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom dynamic dark-mode/glassmorphic CSS style (Restored to the very first beautiful version!)
st.markdown("""
<style>
    .main {
        background-color: #0f111a;
        color: #e2e8f0;
    }
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #0f172a, #020617);
    }
    h1, h2, h3, h4 {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(to right, #60a5fa, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    .card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .thought-card {
        background: rgba(139, 92, 246, 0.1);
        border-left: 4px solid #8b5cf6;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 8px;
        color: #e2e8f0;
    }
    .action-card {
        background: rgba(236, 72, 153, 0.1);
        border-left: 4px solid #ec4899;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 8px;
        color: #e2e8f0;
    }
    .obs-card {
        background: rgba(16, 185, 129, 0.1);
        border-left: 4px solid #10b981;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 8px;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Helper to load LLM based on environment
@st.cache_resource
def load_llm():
    try:
        return get_provider()
    except Exception as e:
        return e

llm = load_llm()

# Title and Description
st.title("💼 Enterprise HR ReAct Agent Workspace")
st.markdown("Interact with the HR Management database using Chatbot Baseline vs ReAct Agent v1 & v2. Powered by local LLM via Ollama.")

# Sidebar - Configuration and Telemetry
st.sidebar.markdown("<h2 style='color:#38bdf8;'>⚙️ Settings & Telemetry</h2>", unsafe_allow_html=True)

# Sidebar System selectbox
system_mode = st.sidebar.selectbox(
    "Choose Agent Model:",
    ["ReAct Agent v2 (Production)", "ReAct Agent v1 (Basic)", "Chatbot Baseline"]
)

# Slider to limit max output tokens
max_tokens = st.sidebar.slider(
    "Limit Output Tokens:",
    min_value=64,
    max_value=2048,
    value=1024,
    step=64,
    help="Maximum tokens the model can generate in a single call."
)

# Slider to limit max ReAct steps
max_steps = st.sidebar.slider(
    "Max ReAct Steps:",
    min_value=1,
    max_value=5,
    value=3,
    step=1,
    help="Maximum number of Thought-Action-Observation loops the ReAct agent is allowed to perform."
)

# Show LLM Provider Details
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔌 Connection Details")
if isinstance(llm, Exception):
    st.sidebar.error(f"Failed to load Provider: {llm}")
    st.sidebar.warning("Please check your .env file. For Ollama: make sure Ollama is running and you've pulled a model.")
else:
    st.sidebar.success(f"Connected to **{llm.provider.upper()}**")
    st.sidebar.info(f"Model: `{llm.model_name}`")

# Performance Dashcard in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Performance Dashboard")

# Track cumulative metrics
if "cumulative_tokens" not in st.session_state:
    st.session_state.cumulative_tokens = 0
if "cumulative_cost" not in st.session_state:
    st.session_state.cumulative_cost = 0.0
if "cumulative_latency" not in st.session_state:
    st.session_state.cumulative_latency = 0
if "queries_run" not in st.session_state:
    st.session_state.queries_run = 0

col1, col2 = st.sidebar.columns(2)
with col1:
    st.markdown("<div class='card'><span class='metric-label'>Total Queries</span><br><span class='metric-value'>{}</span></div>".format(st.session_state.queries_run), unsafe_allow_html=True)
with col2:
    st.markdown("<div class='card'><span class='metric-label'>Est. Cost (USD)</span><br><span class='metric-value'>${:.5f}</span></div>".format(st.session_state.cumulative_cost), unsafe_allow_html=True)

col3, col4 = st.sidebar.columns(2)
with col3:
    st.markdown("<div class='card'><span class='metric-label'>Total Tokens</span><br><span class='metric-value'>{}</span></div>".format(st.session_state.cumulative_tokens), unsafe_allow_html=True)
with col4:
    st.markdown("<div class='card'><span class='metric-label'>Avg Latency</span><br><span class='metric-value'>{}ms</span></div>".format(
        int(st.session_state.cumulative_latency / st.session_state.queries_run) if st.session_state.queries_run > 0 else 0
    ), unsafe_allow_html=True)

# 2. Main Chat Area
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_traces" not in st.session_state:
    st.session_state.last_traces = []

# Display prior chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if user_query := st.chat_input("Hỏi tôi về nhân viên, ngày phép, bảng lương hoặc quy định HR..."):
    # Render user query
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Check LLM connection first
    if isinstance(llm, Exception):
        with st.chat_message("assistant"):
            st.error(f"Error: LLM connection is inactive. {llm}")
    else:
        # Dynamically apply token limit selected by user
        llm.max_tokens = max_tokens
        # Reset current execution tracker metrics
        tracker.session_metrics = []
        
        # Instantiate correct version
        with st.spinner("Processing HR query..."):
            start_time = time.time()
            
            try:
                # 3. Running chosen system mode
                if system_mode == "Chatbot Baseline":
                    system = HRBaselineChatbot(llm=llm)
                    response_text = system.run(user_query)
                    traces = []
                elif system_mode == "ReAct Agent v1 (Basic)":
                    system = ReActAgent(llm=llm, tools=TOOLS_METADATA, max_steps=max_steps, version="v1")
                    response_text = system.run(user_query)
                    traces = getattr(system, "history", [])
                else:  # ReAct Agent v2
                    system = ReActAgent(llm=llm, tools=TOOLS_METADATA, max_steps=max_steps, version="v2")
                    response_text = system.run(user_query)
                    traces = getattr(system, "history", [])
                
                execution_time = int((time.time() - start_time) * 1000)
                
                # Render response
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # Fetch telemetry metrics
                run_metrics = tracker.session_metrics
                prompt_tokens = sum([m["prompt_tokens"] for m in run_metrics])
                completion_tokens = sum([m["completion_tokens"] for m in run_metrics])
                cost = sum([m["cost_estimate"] for m in run_metrics])
                total_tokens = sum([m["total_tokens"] for m in run_metrics])
                
                # Update Session Telemetry
                st.session_state.queries_run += 1
                st.session_state.cumulative_tokens += total_tokens
                st.session_state.cumulative_cost += cost
                st.session_state.cumulative_latency += execution_time
                st.session_state.last_traces = traces
                
                # Force UI reload to update Sidebar counters
                st.rerun()
                
            except Exception as e:
                with st.chat_message("assistant"):
                    st.error(f"Error during agent execution: {e}")

# 3. Dynamic Trace Panel (Rendered if traces are present from the last run)
if st.session_state.last_traces:
    st.markdown("### 🔍 ReAct Reasoning Trace (Thought Process)")
    with st.expander("Show step-by-step reasoning details of the last run", expanded=True):
        for idx, step in enumerate(st.session_state.last_traces):
            st.markdown(f"#### Step {step['step']}:")
            
            # Render Thought
            if step.get("thought"):
                st.markdown(f"<div class='thought-card'><b>Thought:</b> {step['thought']}</div>", unsafe_allow_html=True)
                
            # Render Action
            if step.get("action"):
                st.markdown(f"<div class='action-card'><b>Action:</b> <code>{step['action']}</code></div>", unsafe_allow_html=True)
                
            # Render Observation
            if step.get("observation"):
                st.markdown(f"<div class='obs-card'><b>Observation:</b> {step['observation']}</div>", unsafe_allow_html=True)
            st.markdown("---")