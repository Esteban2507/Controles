"""Minimal stubs for langchain.agents used by agent.py and tests."""

class AgentExecutor:
    def __init__(self, agent=None, tools=None, verbose=False, **kwargs):
        self.agent = agent
        self.tools = tools or []

    def invoke(self, payload: dict):
        # Simple stub returning payload echoed as output
        return {"output": payload.get("input", "")}


def create_openai_tools_agent(llm, tools, prompt):
    # Return a simple callable object or sentinel used by AgentExecutor
    return {"llm": llm, "tools": tools, "prompt": prompt}
