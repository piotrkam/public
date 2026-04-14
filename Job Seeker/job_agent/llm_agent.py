"""
LLM agent adapter — single place that couples the pipeline to a specific SDK.

Currently backed by the Claude Agent SDK (claude_agent_sdk), which requires
the Claude Code CLI and a Claude subscription.

To switch to a different LLM, replace the imports below and provide
compatible implementations of:

    AgentDefinition   — a dataclass / object holding (description, prompt, tools)
    AgentOptions      — options passed to each query call (model, tools, cwd, permission_mode, system_prompt)
    ResultMessage     — the message type whose .result attribute holds the agent's final text output
    query()           — async generator: query(prompt, options) → AsyncIterator[message]

See README.md → "Using a different LLM" for a full migration guide.
"""

from claude_agent_sdk import (
    AgentDefinition,
    query,
    ClaudeAgentOptions as AgentOptions,
    ResultMessage,
)

__all__ = ["AgentDefinition", "query", "AgentOptions", "ResultMessage"]
