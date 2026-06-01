from typing import Dict, Any, List
from src.core.llm_provider import LLMProvider

class HRBaselineChatbot:
    """
    A simple Chatbot Baseline that interacts directly with an LLM.
    It does not have access to any external tools or local HR databases.
    Used as a baseline comparison to demonstrate the limitations of standalone LLMs on domain-specific calculations.
    """
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def get_system_prompt(self) -> str:
        return """
        You are a helpful HR Assistant. You answer questions about company policies and employees.
        Since you do not have access to any external databases or tools, you must answer based purely on your pre-trained knowledge.
        Try your best to answer, but do not make up facts if you do not know the answer.
        """

    def run(self, user_input: str) -> str:
        response = self.llm.generate(user_input, system_prompt=self.get_system_prompt())
        return response.get("content", "Error: No response generated.")