from typing import List
from typing import Literal

from langgraph.graph import MessagesState
from pydantic import BaseModel


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
    observations: List = []
    final_report: str =  ""
    last_node: str = ''
    