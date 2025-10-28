from typing import List, Dict, Any
from typing import Literal

from langchain_core.messages import AnyMessage
from langgraph.graph import MessagesState
from pydantic import BaseModel


# from utils.agent_utils import ToolConfig


class Step(BaseModel):
    title: str = ""
    description: str = ""
    status: Literal["pending", "completed"] = "pending"


class Plan(BaseModel):
    goal: str = ""
    thought: str = ""
    steps: List[Step] = []

class State(MessagesState):
    user_message: str = ""
    plan: Plan
    observations: List
    final_report: List
    # last_node: str = ''
    all_messages: List[AnyMessage] = []
    # tools_messages: List[AnyMessage]


def graph_input_formpt(user_message, plan: Plan = None, observations: List = [], final_report: List = []) -> Dict[
    Any, Any]:
    return {
        "user_message": user_message,
        "plan": plan,
        "observations": observations,
        "final_report": final_report,
        "all_messages": [],
    }
