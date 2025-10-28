from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from graph.advanced_agent.nodes import (
    report_node,
    execute_node,
    create_planner_node,
    update_planner_node
)
from graph.advanced_agent.state import State


def _build_base_graph():
    """Build and return the base state graph with all nodes and edges."""
    builder = StateGraph(State)
    builder.add_edge(START, "create_planner_node")
    builder.add_node("create_planner_node", create_planner_node)
    builder.add_node("update_planner_node", update_planner_node)
    builder.add_node("execute_node", execute_node)
    builder.add_node("report_node", report_node)
    builder.add_edge("report_node", END)


    builder.add_edge("create_planner_node","execute_node")
    builder.add_edge("execute_node", "update_planner_node")
    builder.add_conditional_edges("update_planner_node", route_when_plan_completed,{False:"execute_node",True:"report_node"})
    return builder

def route_when_plan_completed(state: State):
    plan = state['plan']
    if plan and len(plan['steps'][-1]['status'])>0 and plan['steps'][-1]['status'] == 'completed':
        return True
    else:
        return False


def get_graph_builder():
    """Build and return the base state graph with all nodes and edges."""
    base_graph = _build_base_graph()
    return base_graph

def build_graph_with_memory():
    """Build and return the agent workflow graph with memory."""
    memory = MemorySaver()
    builder = _build_base_graph()
    return builder.compile(checkpointer=memory)


def build_graph():
    """Build and return the agent workflow graph without memory."""
    # build state graph
    builder = _build_base_graph()
    return builder.compile()


# if __name__ == '__main__':
#     # inputs = {"user_message": "对所给文档进行分析，生成分析报告，文档路径为student_habits_performance.csv",
#     #           "plan": None,
#     #           "observations": [],
#     #           "final_report": ""}
#
#     inputs = {"user_message": "对用户说hello",
#               "plan": None,
#               "observations": [],
#               "final_report": ""}
#
#     graph.invoke(inputs, {"recursion_limit":100})