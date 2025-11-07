"""LangGraph-based agent for LLM + MCP Server integration.

This module implements an agentic loop using LangGraph that allows an LLM
to make tool calls to an MCP server, receive results, and continue reasoning
until a final answer is provided.
"""

import json
import os
import traceback
from typing import Annotated, Any, AsyncGenerator, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# MCP Client imports
try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client

    MCP_CLIENT_AVAILABLE = True
except ImportError:
    MCP_CLIENT_AVAILABLE = False
    print("Warning: MCP client not available")

# Azure chat wrapper
try:
    from demo_client.azure_chat_wrapper import AzureChatWrapper
except ImportError:
    from azure_chat_wrapper import AzureChatWrapper


# ============================================================================
# STATE DEFINITION
# ============================================================================


class AgentState(TypedDict):
    """State of the agent during execution.

    Attributes:
        messages: Conversation history (uses add_messages reducer to append)
        mcp_session: Active MCP session for tool calls
        mcp_tools_formatted: List of tools in Azure AI Inference format
    """

    messages: Annotated[List[BaseMessage], add_messages]
    mcp_session: Optional[ClientSession]
    mcp_tools_formatted: List[Dict[str, Any]]


# ============================================================================
# LANGGRAPH AGENT
# ============================================================================


class LangGraphAgent:
    """Agent that uses LangGraph to orchestrate LLM and MCP server interactions."""

    def __init__(
        self,
        github_token: Optional[str] = None,
        model: str = "gpt-4o",
    ):
        """Initialize the LangGraph agent.

        Args:
            github_token: GitHub API token for Azure AI Inference
            model: Model to use (default: gpt-4o)
        """
        self.github_token = github_token or os.getenv("GITHUB_API_KEY")
        if not self.github_token:
            raise ValueError("GITHUB_API_KEY required")

        self.model = model

        # Initialize Azure chat wrapper (LangChain-compatible)
        self.llm_client = AzureChatWrapper(
            github_token=self.github_token,
            model=self.model,
            temperature=0.7,
            max_tokens=2000,
        )

        # MCP connection state
        self.mcp_session: Optional[ClientSession] = None
        self.mcp_tools_formatted: List[Dict[str, Any]] = []
        self.mcp_context = None

        # Compiled graph (will be set after connect)
        self.app = None

    def build_graph(self, mcp_server_url: Optional[str] = None):
        """Build the LangGraph workflow (without connecting to MCP yet).

        Args:
            mcp_server_url: MCP server URL (defaults to env MCP_SERVER_URL)
        """
        if not MCP_CLIENT_AVAILABLE:
            raise ImportError("MCP client not available - install 'mcp' package")

        # Format MCP URL (ensure /sse suffix)
        base_url = mcp_server_url or os.getenv("MCP_SERVER_URL", "http://localhost:8001")
        self.mcp_sse_url = base_url if base_url.endswith("/sse") else f"{base_url}/sse"

        print(f"✅ LangGraph agent initialized")
        print(f"📍 MCP server URL: {self.mcp_sse_url}")

        # Build the LangGraph workflow
        self._build_graph()

    def _build_graph(self):
        """Build and compile the LangGraph StateGraph."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("call_llm", self._call_llm)
        workflow.add_node("call_mcp_tools", self._call_mcp_tools)

        # Set entry point
        workflow.set_entry_point("call_llm")

        # Add conditional edge after LLM call
        workflow.add_conditional_edges(
            "call_llm",
            self._should_continue,
            {
                "continue": "call_mcp_tools",  # If tools needed, execute them
                "end": END,  # If final answer, end
            },
        )

        # After calling tools, always go back to LLM
        workflow.add_edge("call_mcp_tools", "call_llm")

        # Compile the graph
        self.app = workflow.compile()
        print("✅ LangGraph workflow compiled")

    # ------------------------------------------------------------------------
    # GRAPH NODES
    # ------------------------------------------------------------------------

    def _call_llm(self, state: AgentState) -> Dict[str, Any]:
        """Node: Call the LLM with current messages and available tools.

        Args:
            state: Current agent state

        Returns:
            Updated state with LLM response
        """
        messages = state["messages"]
        tools = state["mcp_tools_formatted"]

        print(f"  → Node: call_llm (with {len(tools)} tools)")

        # Call LLM via LangChain-compatible wrapper
        # The wrapper handles message format conversion automatically
        response = self.llm_client.invoke(
            messages,
            tools=tools if tools else None,
        )

        # Return the assistant's message (AIMessage with potential tool_calls)
        return {"messages": [response]}

    async def _call_mcp_tools(self, state: AgentState) -> Dict[str, Any]:
        """Node: Execute tool calls requested by the LLM.

        Args:
            state: Current agent state

        Returns:
            Updated state with tool results
        """
        last_message = state["messages"][-1]
        session = state["mcp_session"]

        print(f"  → Node: call_mcp_tools")

        tool_result_messages = []

        # Execute each tool call (LangChain format)
        for tool_call in last_message.tool_calls:
            # LangChain tool_call format: {"id": str, "name": str, "args": dict or str}
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # If args is still a string, parse it
            if isinstance(tool_args, str):
                tool_args = json.loads(tool_args)

            print(f"    ⚙️  Executing: {tool_name}({tool_args})")

            try:
                # Call MCP server
                result = await session.call_tool(tool_name, tool_args)

                # Extract text content
                if hasattr(result, "content") and result.content:
                    if isinstance(result.content, list) and len(result.content) > 0:
                        content_str = result.content[0].text
                    else:
                        content_str = str(result.content)
                else:
                    content_str = str(result)

                print(f"    ✅ Result: {content_str[:100]}...")

            except Exception as e:
                print(f"    ❌ Error: {e}")
                content_str = f"Error executing {tool_name}: {str(e)}"

            # Create ToolMessage for the LLM (LangChain format)
            tool_result_messages.append(
                ToolMessage(content=content_str, tool_call_id=tool_call["id"])
            )

        return {"messages": tool_result_messages}

    def _should_continue(self, state: AgentState) -> str:
        """Conditional edge: Decide whether to continue or end.

        Args:
            state: Current agent state

        Returns:
            "continue" if tools need to be called, "end" otherwise
        """
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            print("  → Decision: continue (tool calls needed)")
            return "continue"
        else:
            print("  → Decision: end (final answer)")
            return "end"

    # ------------------------------------------------------------------------
    # PUBLIC INTERFACE
    # ------------------------------------------------------------------------

    async def astream_response(
        self, user_message: str, system_prompt: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream agent execution events for real-time UI updates.

        This method uses `astream_events` to provide detailed events:
        - on_chat_model_start: LLM starts thinking
        - on_chat_model_stream: LLM streaming response
        - on_chat_model_end: LLM finished
        - on_tool_start: Tool execution starts
        - on_tool_end: Tool execution completes

        Args:
            user_message: User's request
            system_prompt: System prompt with context

        Yields:
            Event dictionaries with type and data
        """
        if not self.app:
            yield {
                "type": "error",
                "data": "Agent not initialized. Call build_graph() first.",
            }
            return

        # Connect to MCP for this request
        try:
            async with sse_client(self.mcp_sse_url) as (mcp_read, mcp_write):
                async with ClientSession(mcp_read, mcp_write) as mcp_session:
                    await mcp_session.initialize()

                    # Get available tools
                    tools_result = await mcp_session.list_tools()
                    mcp_tools_formatted = [
                        {
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.inputSchema,
                            },
                        }
                        for tool in tools_result.tools
                    ]

                    yield {"type": "info", "data": f"🔗 Connected to MCP ({len(mcp_tools_formatted)} tools)"}

                    # Initial state
                    initial_messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=user_message),
                    ]

                    initial_state = {
                        "messages": initial_messages,
                        "mcp_session": mcp_session,
                        "mcp_tools_formatted": mcp_tools_formatted,
                    }

                    # Stream events from graph execution
                    async for event in self.app.astream_events(initial_state, version="v2"):
                        event_kind = event.get("event")
                        event_data = event.get("data", {})
                        event_name = event.get("name", "")

                        # Chat model events
                        if event_kind == "on_chat_model_start":
                            yield {"type": "llm_start", "data": "🧠 LLM thinking..."}

                        elif event_kind == "on_chat_model_stream":
                            # Stream LLM response chunks
                            chunk = event_data.get("chunk", {})
                            if hasattr(chunk, "content") and chunk.content:
                                yield {"type": "llm_stream", "data": chunk.content}

                        elif event_kind == "on_chat_model_end":
                            # LLM finished - check if it wants to call tools
                            output = event_data.get("output", {})
                            if hasattr(output, "tool_calls") and output.tool_calls:
                                for tool_call in output.tool_calls:
                                    # LangChain format: {"id": str, "name": str, "args": dict or str}
                                    tool_name = tool_call["name"]
                                    tool_args = tool_call["args"]
                                    if isinstance(tool_args, str):
                                        tool_args = json.loads(tool_args)
                                    yield {
                                        "type": "tool_call",
                                        "data": {
                                            "name": tool_name,
                                            "arguments": tool_args,
                                        },
                                    }
                            else:
                                # Final response
                                if hasattr(output, "content") and output.content:
                                    yield {"type": "final_answer", "data": output.content}

                        # Custom node events (for call_mcp_tools)
                        elif event_kind == "on_chain_end" and event_name == "call_mcp_tools":
                            # Tool execution finished - extract results from output
                            output = event_data.get("output", {})
                            if isinstance(output, dict) and "messages" in output:
                                messages = output["messages"]
                                for msg in messages:
                                    if hasattr(msg, "content"):
                                        yield {"type": "tool_response", "data": msg.content}

                    yield {"type": "complete", "data": "✨ Request completed"}

        except Exception as e:
            # Log full traceback for debugging
            error_detail = traceback.format_exc()
            print(f"❌ Full error traceback:\n{error_detail}")

            # Yield detailed error for UI
            yield {
                "type": "error",
                "data": f"❌ Error: {str(e)}\n\n```\n{error_detail}\n```"
            }
