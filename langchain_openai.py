"""Stub for langchain_openai ChatOpenAI/AzureChatOpenAI used in tests."""

class ChatOpenAI:
    def __init__(self, model="gpt-4", temperature=0.0, api_key=None, **kwargs):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key


class AzureChatOpenAI(ChatOpenAI):
    def __init__(self, azure_endpoint=None, azure_deployment=None, api_version=None, api_key=None, **kwargs):
        super().__init__(model=azure_deployment, temperature=0.0, api_key=api_key)
        self.azure_endpoint = azure_endpoint
        self.azure_deployment = azure_deployment
        self.api_version = api_version
