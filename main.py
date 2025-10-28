import logging

from concurrent_log_handler import ConcurrentRotatingFileHandler

from graph.advanced_agent.graph import build_graph
from graph.advanced_agent.state import graph_input_formpt
from utils.agent_utils import graph_response
from utils.config_utils import Config

handler = ConcurrentRotatingFileHandler(
    # 日志文件
    Config.LOG_FILE,
    # 日志文件最大允许大小为5MB，达到上限后触发轮转
    maxBytes=Config.MAX_BYTES,
    # 在轮转时，最多保留3个历史日志文件
    backupCount=Config.BACKUP_COUNT
)
format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO,  # 设置根logger的级别
                    format=format,
                    handlers=[handler])  # 添加StreamHandler
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # inputs = {"user_message": "对所给文档进行分析，生成分析报告，文档路径为student_habits_performance.csv",
    #           "plan": None,
    #           "observations": [],
    #           "final_report": ""}

    user_input = "帮我创建一个名为test.py的文件，内容为test123"
    graph_input = graph_input_formpt(user_input)

    graph = build_graph()
    # asyncio.run(graph.astream(graph_input_formpt(user_input), {"recursion_limit":100}))
    config = {"configurable": {"thread_id": "330", "user_id": "330"}}
    graph_response(graph, graph_input, config)
    # asyncio.run(graph_response(graph, graph_input,config))
