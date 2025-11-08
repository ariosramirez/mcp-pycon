"""Streamlit demo app for PyCon presentation.

This interactive web application demonstrates the Model Context Protocol (MCP) in action,
showing how Large Language Models can securely interact with real-world APIs through
an MCP server bridge.

Key Features:
    - Three interactive scenarios demonstrating MCP capabilities
    - Real-time LLM processing with LangGraph agent
    - Visual representation of tool calls and responses
    - Secure API key management (never exposed to LLM)
    - Natural language input in Spanish → Structured API calls

Architecture Flow:
    User Input (Spanish) → LLM (Reasoning) → MCP Server (Secure Bridge) → Task API → S3

The app uses:
    - LangGraph for agentic LLM workflows
    - Azure AI Inference (GitHub Models) for LLM access
    - MCP protocol for secure tool calling
    - Streamlit for interactive UI
"""

import streamlit as st
import time
import os
import asyncio
import json
from datetime import datetime
from typing import List, Optional

# Import LangGraph agent for LLM integration
try:
    from demo_client.langgraph_agent import LangGraphAgent
    from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
    LLM_AVAILABLE = True
except ImportError as e:
    LLM_AVAILABLE = False
    print(f"LangGraph agent import error: {e}")
    # Fallback imports if langchain not available
    try:
        from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
    except ImportError:
        pass

# Page configuration
st.set_page_config(
    page_title="MCP + Task API Demo - PyCon",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .scenario-box {
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    .user-quote {
        font-style: italic;
        padding: 1rem;
        border-left: 4px solid #28a745;
        background-color: #f0fff4;
        margin: 1rem 0;
    }
    .llm-processing {
        padding: 1rem;
        border-left: 4px solid #17a2b8;
        background-color: #e7f7ff;
        margin: 1rem 0;
    }
    .security-highlight {
        padding: 1rem;
        border-left: 4px solid #ffc107;
        background-color: #fff9e6;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scenarios_completed' not in st.session_state:
    st.session_state.scenarios_completed = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []  # Store serialized messages


@st.cache_resource
def get_langgraph_agent() -> Optional[LangGraphAgent]:
    """Initialize and cache the LangGraph agent with MCP connection.

    Returns:
        Initialized LangGraphAgent or None if initialization fails
    """
    if not LLM_AVAILABLE:
        return None

    github_token = os.getenv("GITHUB_API_KEY")
    if not github_token:
        print("⚠️ GITHUB_API_KEY not set")
        return None

    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:8001")

    try:
        agent = LangGraphAgent(github_token=github_token)
        # Build graph (MCP connection happens per-request)
        agent.build_graph(mcp_server_url)
        return agent
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()
        return None


def serialize_message(msg: BaseMessage) -> dict:
    """Serialize a LangChain message to a dictionary for storage in session_state.
    
    Args:
        msg: LangChain message to serialize
        
    Returns:
        Dictionary representation of the message
    """
    msg_dict = {
        "type": msg.__class__.__name__,
        "content": msg.content if hasattr(msg, "content") else str(msg),
    }
    
    # Add tool_calls if present (for AIMessage)
    if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
        msg_dict["tool_calls"] = [
            {
                "id": tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", ""),
                "name": tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", ""),
                "args": tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}),
            }
            for tc in msg.tool_calls
        ]
    
    # Add tool_call_id for ToolMessage
    if isinstance(msg, ToolMessage) and hasattr(msg, "tool_call_id"):
        msg_dict["tool_call_id"] = msg.tool_call_id
    
    return msg_dict


def deserialize_message(msg_dict: dict) -> BaseMessage:
    """Deserialize a dictionary back to a LangChain message.
    
    Args:
        msg_dict: Dictionary representation of the message
        
    Returns:
        LangChain message object
    """
    msg_type = msg_dict.get("type", "HumanMessage")
    content = msg_dict.get("content", "")
    
    if msg_type == "SystemMessage":
        return SystemMessage(content=content)
    elif msg_type == "HumanMessage":
        return HumanMessage(content=content)
    elif msg_type == "AIMessage":
        msg = AIMessage(content=content)
        # Restore tool_calls if present
        if "tool_calls" in msg_dict:
            msg.tool_calls = msg_dict["tool_calls"]
        return msg
    elif msg_type == "ToolMessage":
        tool_call_id = msg_dict.get("tool_call_id", "")
        return ToolMessage(content=content, tool_call_id=tool_call_id)
    else:
        # Fallback to HumanMessage
        return HumanMessage(content=content)


def get_conversation_history() -> List[BaseMessage]:
    """Get the conversation history from session_state as LangChain messages.
    
    Returns:
        List of LangChain messages
    """
    if not st.session_state.conversation_history:
        return []
    return [deserialize_message(msg_dict) for msg_dict in st.session_state.conversation_history]


def save_conversation_history(messages: List[BaseMessage]) -> None:
    """Save conversation history to session_state.
    
    Args:
        messages: List of LangChain messages to save
    """
    st.session_state.conversation_history = [serialize_message(msg) for msg in messages]


def clear_conversation_history() -> None:
    """Clear the conversation history."""
    st.session_state.conversation_history = []


def mark_scenario_complete(scenario_num):
    """Mark a scenario as completed."""
    if scenario_num not in st.session_state.scenarios_completed:
        st.session_state.scenarios_completed.append(scenario_num)


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 MCP + Task API Demo</h1>
        <h3>Bridging LLMs and Real-World APIs Securely</h3>
        <p>PyCon Demo - Model Context Protocol in Action</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with navigation."""
    with st.sidebar:
        st.title("📋 Navigation")

        # Progress metrics
        total_scenarios = 3
        completed = len(st.session_state.scenarios_completed)
        st.metric("Scenarios Completed", f"{completed}/{total_scenarios}")
        st.progress(completed / total_scenarios)

        st.markdown("---")

        # Navigation menu
        pages = {
            "🏠 Home": "Home",
            "📐 Architecture": "Architecture",
            "🎬 Scenario 1": "Scenario 1",
            "🎬 Scenario 2": "Scenario 2",
            "🎬 Scenario 3": "Scenario 3",
            "🎯 Benefits": "Benefits",
            "💻 Implementation": "Implementation",
            "🎓 Conclusion": "Conclusion"
        }

        for label, page in pages.items():
            if st.button(label, key=f"nav_{page}"):
                st.session_state.current_page = page

        st.markdown("---")

        # Completion badges
        st.markdown("### 🏆 Achievements")
        for i in range(1, 4):
            if i in st.session_state.scenarios_completed:
                st.success(f"✅ Scenario {i} Completed")
            else:
                st.info(f"⏳ Scenario {i} Pending")

        st.markdown("---")

        # Reset button
        if st.button("🔄 Reset Demo", type="secondary"):
            st.session_state.scenarios_completed = []
            st.session_state.current_page = "Home"
            st.rerun()


def show_home():
    """Show the home page."""
    render_header()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🌉 Language Barrier")
        st.write("Bridge natural language and HTTP+JSON APIs")

    with col2:
        st.markdown("### 🔒 Security")
        st.write("Secure credential management without exposure")

    with col3:
        st.markdown("### 🎪 Orchestration")
        st.write("Intelligent multi-step workflow execution")

    st.markdown("---")

    st.markdown("""
    ## Welcome to the MCP Demo!

    This interactive demonstration shows how the **Model Context Protocol (MCP)** solves
    three critical problems when integrating Large Language Models with real-world APIs:

    1. **The Language Barrier** - LLMs speak natural language, APIs speak HTTP+JSON
    2. **The Security Dilemma** - How to give API access without exposing credentials
    3. **The Orchestration Burden** - Managing complex multi-step workflows

    ### 🎮 How to Use This Demo

    Use the **sidebar navigation** to explore:
    - **Architecture**: See how all components work together
    - **Scenarios 1-3**: Interactive demonstrations of real workflows
    - **Benefits**: Learn why MCP matters
    - **Implementation**: See the code behind the magic
    - **Conclusion**: Next steps and resources

    👉 **Start with the Architecture page** to understand the system, then run through the scenarios!
    """)

    if st.button("🚀 View Architecture", type="primary"):
        st.session_state.current_page = "Architecture"
        st.rerun()


def show_architecture():
    """Show the architecture page."""
    st.title("📐 Architecture")

    st.markdown("""
    ## System Overview

    The MCP demo implements a secure three-layer architecture that keeps credentials isolated
    while enabling powerful LLM-driven workflows.
    """)

    # Architecture diagram
    st.code("""
    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │   Usuario   │─────▶│   Cliente   │─────▶│ MCP Server  │─────▶│  Task API   │
    │  (Español)  │◀─────│   (LLM)     │◀─────│  (Secure)   │◀─────│  (FastAPI)  │
    └─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
                                │                      │                    │
                                │                      │                    │
                         Natural Language      API Key (Secure)      Stores in S3
                         Understanding         Translation Layer     JSON Files
    """, language="text")

    st.markdown("---")

    # Component details in columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Key Components")
        st.markdown("""
        1. **Usuario**: Gives instructions in natural language (Spanish)
        2. **LLM (Claude)**: Understands intent and selects appropriate tools
        3. **MCP Server**: Secure bridge that injects API credentials
        4. **Task API**: FastAPI service with business logic and validation
        5. **S3 Storage**: Simple, visual data persistence
        """)

    with col2:
        st.markdown("### 🔒 Security Flow")
        st.markdown("""
        - API key stored **only** in MCP Server environment
        - LLM **never** sees the credential
        - MCP Server injects `X-API-Key` header on every request
        - Task API validates the key before processing
        - Complete credential isolation
        """)

    st.markdown("---")

    # Data flow
    with st.expander("🔄 See Detailed Request Flow"):
        st.markdown("""
        #### Step-by-Step Request Flow

        1. **User Input**: "Registra a María García (maria@test-azollon.com)"

        2. **LLM Processing**:
           - Parses natural language
           - Identifies tool: `register_user`
           - Extracts parameters: name, email, company

        3. **MCP Server**:
           - Receives tool call from LLM
           - Injects API key from environment variable
           - Makes HTTP POST to Task API

        4. **Task API**:
           - Validates API key
           - Validates request schema (Pydantic)
           - Generates unique ID
           - Stores user data in S3
           - Returns success response

        5. **Response Chain**:
           - Task API → MCP Server → LLM → User
           - LLM formats response in natural language
        """)

    if st.button("▶️ Run Scenario 1", type="primary"):
        st.session_state.current_page = "Scenario 1"
        st.rerun()


async def process_with_llm(user_message: str, scenario_context: str = "", maintain_context: bool = True):
    """Process user message with LangGraph agent and stream execution events.

    This function connects to the LangGraph agent, which uses an LLM (via GitHub Models)
    to interpret natural language and make tool calls to the MCP server. Events are
    streamed in real-time to show the agent's reasoning process.

    Args:
        user_message: The user's natural language request (e.g., in Spanish)
        scenario_context: Additional context to guide the LLM's behavior for this scenario
        maintain_context: If True, maintains conversation history across multiple executions

    Yields:
        Event dictionaries with structure:
            - type: Event type (info, llm_start, tool_call, tool_response, final_answer, etc.)
            - data: Event-specific data (string, dict, etc.)

    Example:
        async for event in process_with_llm("Registra un nuevo cliente", "Register users"):
            if event["type"] == "tool_call":
                print(f"Tool: {event['data']['name']}")
    """
    agent = get_langgraph_agent()

    if not agent:
        yield {"type": "error", "data": "Agent not available"}
        return

    # Create system prompt with scenario context
    system_prompt = f"""You are demonstrating the Model Context Protocol (MCP) at PyCon.
You have access to tools for managing users, calls, and tasks via an MCP server.

Scenario Context: {scenario_context}

When the user makes a request:
1. Analyze what they're asking for
2. Use the available MCP tools to complete the request
3. Explain each step clearly

Be concise and clear in your explanations."""

    # Get previous conversation history if maintaining context
    previous_messages = None
    if maintain_context:
        previous_messages = get_conversation_history()

    try:
        # Stream events from agent
        final_messages = None
        async for event in agent.astream_response(user_message, system_prompt, previous_messages):
            # Capture conversation state for history persistence
            if event.get("type") == "conversation_state":
                final_messages = event.get("data")
            yield event
        
        # Save conversation history after completion
        if maintain_context and final_messages:
            save_conversation_history(final_messages)
            
    except Exception as e:
        yield {"type": "error", "data": f"❌ Error: {str(e)}"}


def display_llm_events(events: List[dict]) -> None:
    """Display LLM processing events from LangGraph agent in real-time.

    This function visualizes the agent's execution flow, showing:
    - When the LLM starts reasoning
    - Which tools the LLM decides to call
    - The arguments passed to each tool
    - The responses from the MCP server
    - The final natural language response

    Args:
        events: List of event dictionaries from agent.astream_events() with structure:
            - type: Event type (error, info, llm_start, tool_call, tool_response, final_answer, complete)
            - data: Event-specific payload (varies by type)

    Event Types:
        - error: Error message (displayed as st.error)
        - info: Informational message (e.g., "Connected to MCP")
        - llm_start: LLM begins processing
        - llm_stream: Streaming LLM response chunks
        - tool_call: LLM wants to call a tool (shows tool name + arguments)
        - tool_response: Result from tool execution via MCP server
        - final_answer: LLM's final response in natural language
        - complete: Execution finished
    """
    if not events:
        return

    st.markdown("### 🤖 LLM Execution Flow")

    # Process events and display in chronological order
    for event in events:
        event_type = event.get("type")
        event_data = event.get("data")

        if event_type == "error":
            # Show errors prominently
            st.error(event_data)

        elif event_type == "info":
            # System information (e.g., "Connected to MCP with 9 tools")
            st.info(event_data)

        elif event_type == "llm_start":
            # LLM begins reasoning
            st.info(event_data)

        elif event_type == "llm_stream":
            # Streaming LLM response chunks (could be accumulated for real-time effect)
            st.markdown(event_data)

        elif event_type == "tool_call":
            # LLM decided to call a tool - show which one and with what arguments
            tool_name = event_data.get("name")
            tool_args = event_data.get("arguments")
            with st.expander(f"⚙️ Tool Call: `{tool_name}`", expanded=True):
                st.markdown(f"**The LLM is calling `{tool_name}` with these arguments:**")
                st.code(json.dumps(tool_args, indent=2), language="json")

        elif event_type == "tool_start":
            # Tool execution starting
            st.markdown(f"**{event_data}**")

        elif event_type == "tool_response":
            # Tool execution completed - show the result from MCP server
            with st.expander(f"⚙️ Tool Response", expanded=True):
                st.markdown("**Result from MCP Server:**")
                st.markdown(event_data)

        elif event_type == "tool_end":
            # Fallback for older event format
            result_text = event_data.replace("✅ Tool result: ", "")
            with st.expander(f"⚙️ Tool Response", expanded=True):
                st.markdown(result_text)

        elif event_type == "final_answer":
            # LLM's final response after processing tool results
            st.success(f"💬 **Final Response (Natural Language):**\n\n{event_data}")

        elif event_type == "conversation_state":
            # Conversation state saved (handled internally, no UI display needed)
            pass

        elif event_type == "complete":
            # Execution finished
            st.markdown(f"_{event_data}_")


def check_llm_availability() -> bool:
    """Check if LLM integration is properly configured and show helpful errors if not.

    This function verifies:
    1. LangGraph agent module is importable
    2. GitHub API key (for Azure AI Inference) is set
    3. Agent can be initialized

    Returns:
        True if LLM is available and ready, False otherwise (with error message shown to user)
    """
    if not LLM_AVAILABLE:
        st.error("""
        ⚠️ **LLM Integration Not Available**

        The LangGraph agent module could not be imported. This means the LLM
        won't be able to process your requests.

        **To fix this**:
        1. ✅ Install dependencies: `pip install langgraph langchain-core`
        2. ✅ Verify imports work: `python -c "from demo_client.langgraph_agent import LangGraphAgent"`
        3. ✅ Set `GITHUB_API_KEY` environment variable
        4. ✅ Ensure MCP server is running at http://localhost:8001
        5. ✅ Restart the Streamlit app

        **For Docker users**: Make sure the `demo-client` service is properly configured.
        """)
        return False

    # Check if GITHUB_API_KEY is set
    if not os.getenv("GITHUB_API_KEY"):
        st.error("""
        ⚠️ **GitHub API Key Not Configured**

        The demo needs access to GitHub Models (Azure AI Inference) for LLM capabilities.

        **To get started**:
        1. 🔑 Get a free token at: https://github.com/settings/tokens
        2. 📝 Set the environment variable:
           ```bash
           export GITHUB_API_KEY=your-github-token-here
           ```
        3. 🔄 Restart the Streamlit app: `streamlit run demo_client/streamlit_app.py`

        **For Docker users**:
        ```bash
        export GITHUB_API_KEY=your-token
        docker compose up -d --build
        ```

        **Note**: The LLM integration uses GitHub Models, which provides free access to
        various models including GPT-4o. No additional setup required beyond the token!
        """)
        return False

    return True


def show_scenario_1():
    """Show Scenario 1: Register user and schedule call."""
    st.title("🎬 Scenario 1: Register New Client & Schedule Onboarding")

    st.markdown("""
    ### What This Demonstrates
    A typical workflow where we register a new client and immediately schedule their onboarding call.

    **Key Features:**
    - Natural language → Structured API calls
    - Secure API key handling (never exposed to LLM)
    - Multi-step orchestration (register then schedule)
    - Real-world business use case
    """)

    st.markdown("---")

    # Conversation history section
    history_count = len(st.session_state.conversation_history)
    if history_count > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📚 **Conversation Context Active**: {history_count} previous messages will be included for context continuity.")
        with col2:
            if st.button("🗑️ Clear History", key="clear_history_1", help="Clear conversation history to start fresh"):
                clear_conversation_history()
                st.rerun()
    else:
        st.info("💡 **Tip**: After running this scenario, the conversation history will be maintained. Run it again with a different message to see context continuity!")

    st.markdown("---")

    # User input
    st.markdown("### 🎤 User Request (Editable)")

    # Default message
    default_message = """Por favor, registra a nuestro nuevo cliente 'Azollon International' con el contacto María García (maria@test-azollon.com) y agéndale una llamada de onboarding para este viernes a las 10am."""

    # Help text with examples
    with st.expander("💡 What happens + Examples to try", expanded=False):
        st.markdown("""
        **The LLM will automatically**:
        1. 🔍 Parse the natural language request (Spanish)
        2. 🛠️ Call `register_user` tool with extracted data (name, email, company)
        3. 🛠️ Call `schedule_call` tool using the new user ID
        4. ✅ Return confirmation in natural language

        **Try these variations**:

        📝 **Different timing**:
        - "...agéndale una llamada para mañana a las 2pm"
        - "...programa una reunión para la próxima semana"

        📝 **Different client type**:
        - "...registra un prospecto llamado Juan Pérez..."
        - "...añade un partner llamado Tech Solutions..."

        📝 **With additional notes**:
        - "...y agrega una nota: cliente VIP con descuento especial"
        - "...incluye una nota: requiere atención prioritaria"

        📝 **Different languages**:
        - "Please register a new client named John Doe..."
        """)

    # Editable text area
    user_message = st.text_area(
        "✏️ Edit the request below (the LLM will process whatever you write):",
        value=default_message,
        height=120,
        key="user_msg_scenario_1",
        help="Modify this message to test different scenarios. The LLM will interpret your request and call the appropriate tools."
    )

    st.markdown(f"""
    <div class="user-quote">
    📢 User says: "{user_message}"
    </div>
    """, unsafe_allow_html=True)

    # Execute button
    if st.button("▶️ Execute Scenario", type="primary", key="exec_scenario_1"):
        # Check if LLM is available
        if not check_llm_availability():
            return

        st.markdown("### 🤖 LLM Processing...")

        # Process with real LLM - collect events
        scenario_context = "Register a new client and schedule their onboarding call"

        # Collect events directly (nest_asyncio already applied at module level)
        events = []

        async def collect_events_async():
            async for event in process_with_llm(user_message, scenario_context):
                events.append(event)

        # Execute async function (nest_asyncio handles nested loops)
        asyncio.run(collect_events_async())

        if events:
            display_llm_events(events)
        else:
            st.warning("No response from LLM. Please check configuration.")

        # Mark as complete
        mark_scenario_complete(1)
        st.balloons()

        if st.button("➡️ Next: Scenario 2", key="next_to_2"):
            st.session_state.current_page = "Scenario 2"
            st.rerun()


def show_scenario_2():
    """Show Scenario 2: Query and update operations."""
    st.title("🎬 Scenario 2: Query & Update Operations")

    st.markdown("""
    ### What This Demonstrates
    Show how LLMs can retrieve data and make intelligent updates based on queries.

    **Key Features:**
    - List/query operations with filters
    - Data-driven decision making
    - State updates based on query results
    - Handling multiple records
    """)

    st.markdown("---")

    # Conversation history section
    history_count = len(st.session_state.conversation_history)
    if history_count > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📚 **Conversation Context Active**: {history_count} previous messages will be included for context continuity.")
        with col2:
            if st.button("🗑️ Clear History", key="clear_history_2", help="Clear conversation history to start fresh"):
                clear_conversation_history()
                st.rerun()
    else:
        st.info("💡 **Tip**: After running this scenario, the conversation history will be maintained. Run it again with a different message to see context continuity!")

    st.markdown("---")

    # User input
    st.markdown("### 🎤 User Request (Editable)")

    # Default message
    default_message = """Muéstrame todas las llamadas pendientes y marca la primera como completada."""

    # Help text with examples
    with st.expander("💡 What happens + Examples to try", expanded=False):
        st.markdown("""
        **The LLM will automatically**:
        1. 🔍 Call `list_calls` tool with optional filters (status, user_id)
        2. 🧠 Process the results and identify relevant calls
        3. 🛠️ Call `update_call_status` tool to change status
        4. ✅ Return summary of actions taken

        **Available filters**:
        - Status: `scheduled`, `completed`, `cancelled`, `rescheduled`
        - User ID: Filter by specific client

        **Try these variations**:

        📝 **Different queries**:
        - "Muéstrame todas las llamadas completadas esta semana"
        - "Lista todas las llamadas del cliente con ID abc-123"
        - "¿Cuántas llamadas tengo programadas para mañana?"

        📝 **Different updates**:
        - "Marca todas las llamadas de hoy como completadas"
        - "Cancela la llamada con ID call-456"
        - "Cambia el estado de la última llamada a rescheduled"

        📝 **Query + Update**:
        - "Busca llamadas pendientes de María y márcalas como completadas"
        - "Show me all scheduled calls and cancel the oldest one"
        """)

    # Editable text area
    user_message = st.text_area(
        "✏️ Edit the request below (test different queries and updates):",
        value=default_message,
        height=120,
        key="user_msg_scenario_2",
        help="The LLM will query the data, process results, and perform updates as requested."
    )

    st.markdown(f"""
    <div class="user-quote">
    📢 User says: "{user_message}"
    </div>
    """, unsafe_allow_html=True)

    # Execute button
    if st.button("▶️ Execute Scenario", type="primary", key="exec_scenario_2"):
        # Check if LLM is available
        if not check_llm_availability():
            return

        st.markdown("### 🤖 LLM Processing...")

        # Process with real LLM - collect events
        scenario_context = "Query scheduled calls and update their status"

        # Collect events directly (nest_asyncio already applied at module level)
        events = []

        async def collect_events_async():
            async for event in process_with_llm(user_message, scenario_context):
                events.append(event)

        # Execute async function (nest_asyncio handles nested loops)
        asyncio.run(collect_events_async())

        if events:
            display_llm_events(events)
        else:
            st.warning("No response from LLM. Please check configuration.")

        # Mark as complete
        mark_scenario_complete(2)
        st.balloons()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back to Scenario 1", key="back_to_1"):
                st.session_state.current_page = "Scenario 1"
                st.rerun()
        with col2:
            if st.button("➡️ Next: Scenario 3", key="next_to_3"):
                st.session_state.current_page = "Scenario 3"
                st.rerun()


def show_scenario_3():
    """Show Scenario 3: Complex workflow orchestration."""
    st.title("🎬 Scenario 3: Complex Workflow Orchestration")

    st.markdown("""
    ### What This Demonstrates
    Demonstrate how MCP handles complex, multi-step operations that require intelligent orchestration.

    **Key Features:**
    - Multi-step workflow planning
    - Cross-entity operations (calls → users → tasks)
    - Intelligent data processing (deduplication)
    - Complex business logic execution
    """)

    st.markdown("---")

    # Conversation history section
    history_count = len(st.session_state.conversation_history)
    if history_count > 0:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📚 **Conversation Context Active**: {history_count} previous messages will be included for context continuity.")
        with col2:
            if st.button("🗑️ Clear History", key="clear_history_3", help="Clear conversation history to start fresh"):
                clear_conversation_history()
                st.rerun()
    else:
        st.info("💡 **Tip**: After running this scenario, the conversation history will be maintained. Run it again with a different message to see context continuity!")

    st.markdown("---")

    # User input
    st.markdown("### 🎤 User Request (Editable)")

    # Default message
    default_message = """Crea una tarea de seguimiento para todos los clientes que tienen llamadas programadas esta semana."""

    # Help text with examples
    with st.expander("💡 What happens + Examples to try", expanded=False):
        st.markdown("""
        **The LLM will automatically orchestrate**:
        1. 🔍 Call `list_calls` tool to get calls matching criteria (this week)
        2. 🧠 Extract unique user IDs from the results
        3. 🛠️ Call `create_task` tool for each unique user
        4. 🎯 Avoid duplicates (intelligent deduplication)
        5. ✅ Return summary of all tasks created

        **This demonstrates**:
        - Multi-step workflow planning
        - Cross-entity operations (calls → users → tasks)
        - Data aggregation and processing
        - Complex business logic execution

        **Try these complex workflows**:

        📝 **Different criteria**:
        - "Crea tareas de preparación para todas las llamadas de mañana"
        - "Para cada cliente con llamadas canceladas, crea una tarea de seguimiento"
        - "Create follow-up tasks for all clients with completed calls this month"

        📝 **With conditions**:
        - "Si un cliente tiene más de 2 llamadas programadas, crea una tarea de revisión"
        - "Crea tareas prioritarias para clientes VIP con llamadas esta semana"

        📝 **Multi-action workflows**:
        - "Lista usuarios sin llamadas y créales una tarea de contacto inicial"
        - "Para cada llamada pendiente, crea una tarea y envía una nota al cliente"
        """)

    # Editable text area
    user_message = st.text_area(
        "✏️ Edit the request below (test complex multi-step workflows):",
        value=default_message,
        height=120,
        key="user_msg_scenario_3",
        help="The LLM will plan and execute complex workflows involving multiple tools and data processing."
    )

    st.markdown(f"""
    <div class="user-quote">
    📢 User says: "{user_message}"
    </div>
    """, unsafe_allow_html=True)

    # Execute button
    if st.button("▶️ Execute Scenario", type="primary", key="exec_scenario_3"):
        # Check if LLM is available
        if not check_llm_availability():
            return

        st.markdown("### 🤖 LLM Processing...")

        # Process with real LLM - collect events
        scenario_context = "Create follow-up tasks for clients with scheduled calls - complex multi-step workflow"

        # Collect events directly (nest_asyncio already applied at module level)
        events = []

        async def collect_events_async():
            async for event in process_with_llm(user_message, scenario_context):
                events.append(event)

        # Execute async function (nest_asyncio handles nested loops)
        asyncio.run(collect_events_async())

        if events:
            display_llm_events(events)
        else:
            st.warning("No response from LLM. Please check configuration.")

        # Mark as complete
        mark_scenario_complete(3)
        st.balloons()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Back to Scenario 2", key="back_to_2"):
                st.session_state.current_page = "Scenario 2"
                st.rerun()
        with col2:
            if st.button("➡️ Next: Benefits", key="next_to_benefits"):
                st.session_state.current_page = "Benefits"
                st.rerun()


def show_benefits():
    """Show the benefits of MCP architecture."""
    st.title("🎯 Why MCP Matters")

    st.markdown("## The Three Core Problems - SOLVED")

    # Problem-solution pairs
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🌉 Language Barrier")
        st.markdown("**Problem:**")
        st.write("LLM speaks natural language, API speaks HTTP+JSON")

        st.markdown("**MCP Solution:**")
        st.success("""
        - LLM sees clean, documented tools
        - MCP translates to HTTP requests
        - Bidirectional communication made simple
        """)

    with col2:
        st.markdown("### 🔒 Security Dilemma")
        st.markdown("**Problem:**")
        st.write("How to give LLM API access without exposing keys?")

        st.markdown("**MCP Solution:**")
        st.success("""
        - API key lives only in MCP server
        - Never sent to LLM or client
        - Secure injection on every request
        - Centralized credential management
        """)

    with col3:
        st.markdown("### 🎪 Orchestration Burden")
        st.markdown("**Problem:**")
        st.write("Where does the business logic live?")

        st.markdown("**MCP Solution:**")
        st.success("""
        - LLM handles high-level reasoning
        - MCP provides tool abstractions
        - API enforces business rules
        - Clean separation of concerns
        """)

    st.markdown("---")

    # Real-world benefits
    st.markdown("## 🌟 Real-World Benefits")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ✅ **Security**: Credentials never exposed
        ✅ **Modularity**: Easy to add/remove tools
        ✅ **Scalability**: Each component scales independently
        """)

    with col2:
        st.markdown("""
        ✅ **Maintainability**: Changes isolated to relevant layers
        ✅ **Flexibility**: Swap LLMs, APIs, or servers without rewriting
        ✅ **Auditability**: All tool calls logged and traceable
        """)

    st.markdown("---")

    # Perfect for
    st.markdown("## 🎯 Perfect For")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.info("**Internal Tools**\n\nIntegrate company APIs securely")

    with col2:
        st.info("**Multi-Service**\n\nOrchestrate multiple services")

    with col3:
        st.info("**Secure Agents**\n\nBuild safe agent architectures")

    with col4:
        st.info("**Enterprise AI**\n\nDeploy at scale with confidence")

    if st.button("💻 See Implementation Details", type="primary"):
        st.session_state.current_page = "Implementation"
        st.rerun()


def show_implementation():
    """Show implementation highlights."""
    st.title("💻 Implementation Highlights")

    tab1, tab2, tab3 = st.tabs(["🔧 MCP Server", "⚡ Task API", "📊 Architecture Stats"])

    with tab1:
        st.markdown("### MCP Server (The Bridge)")
        st.markdown("The MCP server uses **FastMCP** to expose tools that the LLM can call:")

        st.code("""
@mcp.tool
async def register_user(
    name: Annotated[str, "User's full name"],
    email: Annotated[str, "User's email address"],
    company: Annotated[str, "Company name"]
) -> str:
    \"\"\"Register a new user in the system.\"\"\"

    # 🔒 API key injected here (secure!)
    client = httpx.AsyncClient(
        base_url=API_URL,
        headers={"X-API-Key": API_KEY}  # ← Never leaves server
    )

    # 🎯 Clean tool → HTTP translation
    response = await client.post("/users", json={
        "name": name,
        "email": email,
        "company": company
    })

    response.raise_for_status()
    user = response.json()

    return f"✅ User registered: {user['name']} (ID: {user['id']})"
        """, language="python")

        st.info("**Key Point:** The API key is loaded from environment variables and never exposed to the LLM!")

    with tab2:
        st.markdown("### Task API (FastAPI)")
        st.markdown("The Task API handles business logic, validation, and storage:")

        st.code("""
@app.post("/users")
async def create_user(
    user: UserCreate,
    api_key: str = Header(..., alias="X-API-Key")  # ← Validated
):
    # 🛡️ Security check
    verify_api_key(api_key)

    # ✅ Pydantic validation (automatic)
    new_user = User(**user.model_dump())

    # 💾 Store in S3
    storage.save("users", new_user.id, new_user)

    return new_user
        """, language="python")

        st.info("**Key Point:** FastAPI + Pydantic provide automatic validation and type safety!")

    with tab3:
        st.markdown("### Architecture Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Lines of Code", "~800", help="Complete production-ready system")

        with col2:
            st.metric("Components", "3", help="Task API, MCP Server, Demo Client")

        with col3:
            st.metric("API Endpoints", "12", help="CRUD operations for users, calls, tasks")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📦 Key Technologies")
            st.markdown("""
            - **FastAPI**: Modern Python web framework
            - **FastMCP**: Simplified MCP server creation
            - **Pydantic**: Data validation and settings
            - **AWS S3**: Simple, scalable storage
            - **Docker**: Containerization
            - **Streamlit**: Interactive demos
            """)

        with col2:
            st.markdown("#### 🎯 Design Principles")
            st.markdown("""
            - **Security First**: Credential isolation
            - **Type Safety**: Full typing with mypy
            - **Clean Architecture**: Separation of concerns
            - **Cloud Native**: AWS-ready deployment
            - **Developer Experience**: Simple, intuitive APIs
            - **Production Ready**: Error handling, logging
            """)

    if st.button("🎓 View Conclusion", type="primary"):
        st.session_state.current_page = "Conclusion"
        st.rerun()


def show_conclusion():
    """Show conclusion and next steps."""
    st.title("🎓 Conclusion")

    st.markdown("## What We Demonstrated")

    st.success("""
    ✨ **A complete, real-world MCP implementation**

    From natural language in Spanish → Secure API calls → Data in S3
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🌉 Language Barrier")
        st.write("✅ Solved with MCP tools")

    with col2:
        st.markdown("### 🔒 Security")
        st.write("✅ Centralized credentials")

    with col3:
        st.markdown("### 🎪 Orchestration")
        st.write("✅ LLM reasoning + MCP")

    st.markdown("---")

    # Next steps
    st.markdown("## 🚀 Next Steps")

    tab1, tab2 = st.tabs(["🔧 Extend", "📚 Resources"])

    with tab1:
        st.markdown("### Extend the System")

        st.markdown("""
        **Add More Tools:**
        - Email notifications (SendGrid, SES)
        - Slack integration
        - Calendar sync (Google Calendar, Outlook)
        - Payment processing (Stripe)
        - Database connections (PostgreSQL, MongoDB)

        **Build Multi-Agent Systems:**
        - Specialized agents for different domains
        - Agent collaboration and handoffs
        - Shared context and memory

        **Integrate Your APIs:**
        - Existing company services
        - Third-party APIs
        - Custom business logic
        """)

    with tab2:
        st.markdown("### Resources")

        st.markdown("""
        **Documentation:**
        - [MCP Official Docs](https://modelcontextprotocol.io)
        - [FastAPI Documentation](https://fastapi.tiangolo.com)
        - [FastMCP Guide](https://github.com/jlowin/fastmcp)
        - [AWS App Runner](https://aws.amazon.com/apprunner)

        **This Demo:**
        - [GitHub Repository](https://github.com/yourrepo/mcp-pycon-demo)
        - [Slides](https://yoursite.com/pycon-slides)
        - [Video Tutorial](https://yoursite.com/tutorial)

        **Community:**
        - [MCP Discord](https://discord.gg/mcp)
        - [Anthropic Community](https://community.anthropic.com)
        """)

    st.markdown("---")

    # Thank you
    st.markdown("""
    <div class="main-header">
        <h1>¡Gracias por su atención!</h1>
        <h3>Thank You!</h3>
        <p>Questions? Let's chat about building AI agents the right way! 🚀</p>
    </div>
    """, unsafe_allow_html=True)

    # Final metrics
    if len(st.session_state.scenarios_completed) == 3:
        st.success("🎉 **Congratulations!** You've completed all scenarios!")
        st.balloons()


# Main app logic
def main():
    """Main application logic."""
    render_sidebar()

    # Route to current page
    page = st.session_state.current_page

    if page == "Home":
        show_home()
    elif page == "Architecture":
        show_architecture()
    elif page == "Scenario 1":
        show_scenario_1()
    elif page == "Scenario 2":
        show_scenario_2()
    elif page == "Scenario 3":
        show_scenario_3()
    elif page == "Benefits":
        show_benefits()
    elif page == "Implementation":
        show_implementation()
    elif page == "Conclusion":
        show_conclusion()


if __name__ == "__main__":
    main()
