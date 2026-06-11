"""Stubs for tool-related base classes used by agent.py."""

class BaseTool:
    name: str = "base_tool"
    description: str = "Base tool"

    def _run(self, *args, **kwargs):
        raise NotImplementedError()
