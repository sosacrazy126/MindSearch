import copy
from typing import List, Union

from lagent.agents import Agent, AgentForInternLM, AsyncAgent, AsyncAgentForInternLM
from lagent.schema import AgentMessage, AgentStatusCode, ModelStatusCode


class StreamingAgentMixin:
    """Make agent calling output a streaming response."""

    def __call__(self, *message: Union[AgentMessage, List[AgentMessage]], session_id=0, **kwargs):
        for hook in self._hooks.values():
            message = copy.deepcopy(message)
            result = hook.before_agent(self, message, session_id)
            if result:
                message = result
        self.update_memory(message, session_id=session_id)
        response_message = AgentMessage(sender=self.name, content="")
        for response_message in self.forward(*message, session_id=session_id, **kwargs):
            if not isinstance(response_message, AgentMessage):
                model_state, response = response_message
                response_message = AgentMessage(
                    sender=self.name,
                    content=response,
                    stream_state=model_state,
                )
            yield response_message.model_copy()
        self.update_memory(response_message, session_id=session_id)
        for hook in self._hooks.values():
            response_message = response_message.model_copy(deep=True)
            result = hook.after_agent(self, response_message, session_id)
            if result:
                response_message = result
        yield response_message


class AsyncStreamingAgentMixin:
    """Make asynchronous agent calling output a streaming response."""

    async def __call__(
        self, *message: Union[AgentMessage, List[AgentMessage]], session_id=0, **kwargs
    ):
        for hook in self._hooks.values():
            message = copy.deepcopy(message)
            result = hook.before_agent(self, message, session_id)
            if result:
                message = result
        self.update_memory(message, session_id=session_id)
        response_message = AgentMessage(sender=self.name, content="")
        async for response_message in self.forward(*message, session_id=session_id, **kwargs):
            if not isinstance(response_message, AgentMessage):
                model_state, response = response_message
                response_message = AgentMessage(
                    sender=self.name,
                    content=response,
                    stream_state=model_state,
                )
            yield response_message.model_copy()
        self.update_memory(response_message, session_id=session_id)
        for hook in self._hooks.values():
            response_message = response_message.model_copy(deep=True)
            result = hook.after_agent(self, response_message, session_id)
            if result:
                response_message = result
        yield response_message


class StreamingAgent(StreamingAgentMixin, Agent):
    """Base streaming agent class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure plugin_executor is available for tool execution
        if not hasattr(self, 'plugin_executor') and hasattr(self, 'plugins') and self.plugins:
            from lagent.actions.action_executor import ActionExecutor
            self.plugin_executor = ActionExecutor(self.plugins)

    def forward(self, *message: AgentMessage, session_id=0, **kwargs):
        formatted_messages = self.aggregator.aggregate(
            self.memory.get(session_id),
            self.name,
            self.output_format,
            self.template,
        )
        for model_state, response, _ in self.llm.stream_chat(
            formatted_messages, session_id=session_id, **kwargs
        ):
            yield AgentMessage(
                sender=self.name,
                content=response,
                formatted=self.output_format.parse_response(response),
                stream_state=model_state,
            ) if self.output_format else (model_state, response)


class AsyncStreamingAgent(AsyncStreamingAgentMixin, AsyncAgent):
    """Base asynchronous streaming agent class"""

    async def forward(self, *message: AgentMessage, session_id=0, **kwargs):
        formatted_messages = self.aggregator.aggregate(
            self.memory.get(session_id),
            self.name,
            self.output_format,
            self.template,
        )
        async for model_state, response, _ in self.llm.stream_chat(
            formatted_messages, session_id=session_id, **kwargs
        ):
            yield AgentMessage(
                sender=self.name,
                content=response,
                formatted=self.output_format.parse_response(response),
                stream_state=model_state,
            ) if self.output_format else (model_state, response)


class StreamingAgentForInternLM(StreamingAgentMixin, AgentForInternLM):
    """Streaming implementation of `lagent.agents.AgentForInternLM`"""

    _INTERNAL_AGENT_CLS = StreamingAgent

    def __init__(self, *args, **kwargs):
        """Initialize with proper plugin executor setup."""
        # First call parent to create the inner agent
        super().__init__(*args, **kwargs)

        # CRITICAL FIX: Ensure the inner agent has the plugin_executor
        # This must happen AFTER super().__init__() creates self.agent
        # The plugins are stored in self.plugin_executor.actions, not self.plugins

        if hasattr(self, 'plugin_executor') and self.plugin_executor and hasattr(self, 'agent'):
            # The outer plugin_executor already has the initialized actions
            if not hasattr(self.agent, 'plugin_executor') or self.agent.plugin_executor is None:
                # Simply assign the same plugin_executor to the inner agent
                self.agent.plugin_executor = self.plugin_executor
                logging.info("✅ StreamingAgentForInternLM: Fixed inner agent plugin_executor")

            # Also ensure interpreter_executor exists on inner agent
            if not hasattr(self.agent, 'interpreter_executor'):
                self.agent.interpreter_executor = None

    def forward(self, message: AgentMessage, session_id=0, **kwargs):
        if isinstance(message, str):
            message = AgentMessage(sender="user", content=message)
        for _ in range(self.max_turn):
            last_agent_state = AgentStatusCode.SESSION_READY
            for message in self.agent(message, session_id=session_id, **kwargs):
                if isinstance(message.formatted, dict) and message.formatted.get("tool_type"):
                    if message.stream_state == ModelStatusCode.END:
                        message.stream_state = last_agent_state + int(
                            last_agent_state
                            in [
                                AgentStatusCode.CODING,
                                AgentStatusCode.PLUGIN_START,
                            ]
                        )
                    else:
                        message.stream_state = (
                            AgentStatusCode.PLUGIN_START
                            if message.formatted["tool_type"] == "plugin"
                            else AgentStatusCode.CODING
                        )
                else:
                    message.stream_state = AgentStatusCode.STREAM_ING
                yield message
                last_agent_state = message.stream_state
            if self.finish_condition(message):
                message.stream_state = AgentStatusCode.END
                yield message
                return
            if message.formatted["tool_type"]:
                tool_type = message.formatted["tool_type"]
                executor = getattr(self, f"{tool_type}_executor", None)
                if not executor:
                    raise RuntimeError(f"No available {tool_type} executor")
                tool_return = executor(message, session_id=session_id)
                tool_return.stream_state = message.stream_state + 1
                message = tool_return
                yield message
            else:
                message.stream_state = AgentStatusCode.STREAM_ING
                yield message


class AsyncStreamingAgentForInternLM(AsyncStreamingAgentMixin, AsyncAgentForInternLM):
    """Streaming implementation of `lagent.agents.AsyncAgentForInternLM`"""

    _INTERNAL_AGENT_CLS = AsyncStreamingAgent

    def __init__(self, *args, **kwargs):
        """Initialize with proper plugin executor setup."""
        # First call parent to create the inner agent
        super().__init__(*args, **kwargs)

        # CRITICAL FIX: Ensure the inner agent has the plugin_executor
        # This must happen AFTER super().__init__() creates self.agent
        # The plugins are stored in self.plugin_executor.actions, not self.plugins

        if hasattr(self, 'plugin_executor') and self.plugin_executor and hasattr(self, 'agent'):
            # The outer plugin_executor already has the initialized actions
            if not hasattr(self.agent, 'plugin_executor') or self.agent.plugin_executor is None:
                # Simply assign the same plugin_executor to the inner agent
                self.agent.plugin_executor = self.plugin_executor
                print(f"✅ AsyncStreamingAgentForInternLM: Fixed inner agent plugin_executor")

            # Also ensure interpreter_executor exists on inner agent
            if not hasattr(self.agent, 'interpreter_executor'):
                self.agent.interpreter_executor = None

    async def forward(self, message: AgentMessage, session_id=0, **kwargs):
        if isinstance(message, str):
            message = AgentMessage(sender="user", content=message)
        for _ in range(self.max_turn):
            last_agent_state = AgentStatusCode.SESSION_READY
            async for message in self.agent(message, session_id=session_id, **kwargs):
                if isinstance(message.formatted, dict) and message.formatted.get("tool_type"):
                    if message.stream_state == ModelStatusCode.END:
                        message.stream_state = last_agent_state + int(
                            last_agent_state
                            in [
                                AgentStatusCode.CODING,
                                AgentStatusCode.PLUGIN_START,
                            ]
                        )
                    else:
                        message.stream_state = (
                            AgentStatusCode.PLUGIN_START
                            if message.formatted["tool_type"] == "plugin"
                            else AgentStatusCode.CODING
                        )
                else:
                    message.stream_state = AgentStatusCode.STREAM_ING
                yield message
                last_agent_state = message.stream_state
            if self.finish_condition(message):
                message.stream_state = AgentStatusCode.END
                yield message
                return
            if message.formatted["tool_type"]:
                tool_type = message.formatted["tool_type"]
                executor = getattr(self, f"{tool_type}_executor", None)
                if not executor:
                    raise RuntimeError(f"No available {tool_type} executor")
                tool_return = await executor(message, session_id=session_id)
                tool_return.stream_state = message.stream_state + 1
                message = tool_return
                yield message
            else:
                message.stream_state = AgentStatusCode.STREAM_ING
                yield message
