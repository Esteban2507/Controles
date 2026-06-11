"""Stubs for prompt-related classes used by agent.py."""

class ChatPromptTemplate:
    @staticmethod
    def from_messages(messages):
        return {"messages": messages}


class MessagesPlaceholder:
    def __init__(self, variable_name="agent_scratchpad"):
        self.variable_name = variable_name
