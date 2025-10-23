import asyncio

from graph.advanced_agent.graph import build_graph

if __name__ == '__main__':
    # inputs = {"user_message": "对所给文档进行分析，生成分析报告，文档路径为student_habits_performance.csv",
    #           "plan": None,
    #           "observations": [],
    #           "final_report": ""}

    inputs = {"user_message": "帮我创建一个名为test.py的文件，内容为test123",
              "plan": None,
              "observations": [],
              "final_report": ""}

    graph = build_graph()
    asyncio.run(graph.ainvoke(inputs, {"recursion_limit":100}))