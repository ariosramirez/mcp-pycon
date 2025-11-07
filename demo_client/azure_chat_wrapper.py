"""Wrapper for Azure AI Inference to work with LangChain/LangGraph.

This module provides a BaseChatModel-compatible wrapper around Azure's
ChatCompletionsClient so it can be used with LangGraph's message handling.
"""

from typing import Any, Dict, Iterator, List, Optional

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    ChatCompletions,
    SystemMessage as AzureSystemMessage,
    ToolMessage as AzureToolMessage,
    UserMessage as AzureUserMessage,
)
from azure.core.credentials import AzureKeyCredential
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool


class AzureChatWrapper(BaseChatModel):
    """LangChain-compatible wrapper for Azure AI Inference ChatCompletionsClient.

    This wrapper allows Azure's chat client to work with LangGraph by converting
    between LangChain message formats and Azure message formats.
    """

    client: ChatCompletionsClient
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2000

    def __init__(
        self,
        github_token: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ):
        """Initialize the Azure chat wrapper.

        Args:
            github_token: GitHub API token for Azure AI Inference
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional arguments
        """
        endpoint = "https://models.inference.ai.azure.com"
        client = ChatCompletionsClient(
            endpoint=endpoint, credential=AzureKeyCredential(github_token)
        )

        super().__init__(
            client=client,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "azure-ai-inference"

    def _convert_message_to_azure(self, message: BaseMessage) -> Any:
        """Convert LangChain message to Azure message format.

        Args:
            message: LangChain message

        Returns:
            Azure AI Inference message
        """
        if isinstance(message, SystemMessage):
            return AzureSystemMessage(content=message.content)
        elif isinstance(message, HumanMessage):
            return AzureUserMessage(content=message.content)
        elif isinstance(message, AIMessage):
            # Check if this is a tool call message
            if message.tool_calls:
                return AssistantMessage(
                    content=message.content or "",
                    tool_calls=[
                        {
                            "id": tc.get("id", f"call_{i}"),
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": str(tc.get("args", {})),
                            },
                        }
                        for i, tc in enumerate(message.tool_calls)
                    ],
                )
            return AssistantMessage(content=message.content or "")
        elif isinstance(message, ToolMessage):
            return AzureToolMessage(
                content=message.content,
                tool_call_id=message.tool_call_id or "unknown",
            )
        else:
            raise ValueError(f"Unsupported message type: {type(message)}")

    def _convert_azure_to_message(self, azure_message: Any) -> AIMessage:
        """Convert Azure message to LangChain AIMessage.

        Args:
            azure_message: Azure AI Inference message

        Returns:
            LangChain AIMessage
        """
        content = azure_message.content or ""

        # Check for tool calls
        tool_calls = []
        if hasattr(azure_message, "tool_calls") and azure_message.tool_calls:
            for tc in azure_message.tool_calls:
                # Parse arguments if they're a string (Azure returns JSON string)
                args = tc.function.arguments
                if isinstance(args, str):
                    import json
                    args = json.loads(args)

                tool_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "args": args,  # Now a dict, as LangChain expects
                    }
                )

        # Return AIMessage with or without tool_calls
        # LangChain doesn't accept None for tool_calls, so omit if empty
        if tool_calls:
            return AIMessage(content=content, tool_calls=tool_calls)
        else:
            return AIMessage(content=content)

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completion.

        Args:
            messages: List of LangChain messages
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments (tools, etc.)

        Returns:
            ChatResult with the response
        """
        # Convert messages to Azure format
        azure_messages = [self._convert_message_to_azure(msg) for msg in messages]

        # Extract tools if provided
        tools = kwargs.get("tools")
        azure_tools = None
        if tools:
            azure_tools = self._format_tools(tools)

        # Call Azure API
        response: ChatCompletions = self.client.complete(
            messages=azure_messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            tools=azure_tools,
        )

        # Convert response to LangChain format
        choice = response.choices[0]
        message = self._convert_azure_to_message(choice.message)

        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def _format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format tools for Azure API.

        Args:
            tools: List of tool definitions

        Returns:
            Azure-formatted tools
        """
        # Tools are already in the right format from MCP
        return tools

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return identifying parameters."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
