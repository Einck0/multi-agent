import logging
import os
from typing import Dict, Any, List

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import MessagesState

from utils.tools import load_yaml_config, message_to_dict

# 设置日志模版
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 模型配置字典
MODEL_CONFIGS = load_yaml_config()

# 默认配置
DEFAULT_LLM_TYPE = "openai"
DEFAULT_TEMPERATURE = 0.7


class LLMInitializationError(Exception):
    """自定义异常类用于LLM初始化错误"""
    pass


def initialize_llm(llm_type: str = DEFAULT_LLM_TYPE) -> tuple[ChatOpenAI, OpenAIEmbeddings]:
    """
    初始化LLM实例

    Args:
        llm_type (str): LLM类型，可选值为 'openai', 'oneapi', 'qwen', 'ollama'

    Returns:
        ChatOpenAI: 初始化后的LLM实例

    Raises:
        LLMInitializationError: 当LLM初始化失败时抛出
    """
    try:
        # 检查llm_type是否有效
        if llm_type not in MODEL_CONFIGS["llm"]:
            raise ValueError(f"不支持的LLM类型: {llm_type}. 可用的类型: {list(MODEL_CONFIGS["llm"].keys())}")

        config = MODEL_CONFIGS["llm"][llm_type]

        # 特殊处理ollama类型
        if llm_type == "ollama":
            os.environ["OPENAI_API_KEY"] = "NA"

        # 创建LLM实例
        llm_chat = ChatOpenAI(
            base_url=config["OPENAI_API_BASE"],
            api_key=config["OPENAI_API_KEY"],
            model=config["DEFAULT_MODEL"],
            temperature=DEFAULT_TEMPERATURE,
            timeout=30,  # 添加超时配置（秒）
            max_retries=2  # 添加重试次数
        )
        embeddings_config = MODEL_CONFIGS['embeddings'][llm_type] if MODEL_CONFIGS['embedding'][
            'ENABLE_SEPARATE_EMBEDDING'] else MODEL_CONFIGS['llm'][llm_type]
        llm_embedding = OpenAIEmbeddings(
            base_url=embeddings_config["OPENAI_API_BASE"],
            api_key=embeddings_config["OPENAI_API_KEY"],
            model=embeddings_config["DEFAULT_EMBEDDING_MODEL"],
            deployment=embeddings_config["DEFAULT_EMBEDDING_MODEL"],
        )

        logger.info(f"成功初始化 {llm_type} LLM")
        return llm_chat, llm_embedding

    except ValueError as ve:
        logger.error(f"LLM配置错误: {str(ve)}")
        raise LLMInitializationError(f"LLM配置错误: {str(ve)}")
    except Exception as e:
        logger.error(f"初始化LLM失败: {str(e)}")
        raise LLMInitializationError(f"初始化LLM失败: {str(e)}")


def get_llm(llm_type: str = DEFAULT_LLM_TYPE) -> ChatOpenAI:
    """
    获取LLM实例的封装函数，提供默认值和错误处理

    Args:
        llm_type (str): LLM类型

    Returns:
        ChatOpenAI: LLM实例
    """
    try:
        return initialize_llm(llm_type)
    except LLMInitializationError as e:
        logger.warning(f"使用默认配置重试: {str(e)}")
        if llm_type != DEFAULT_LLM_TYPE:
            return initialize_llm(DEFAULT_LLM_TYPE)
        raise  # 如果默认配置也失败，则抛出异常


def llm_invoke(state: MessagesState, llm: BaseChatModel, input: List[BaseMessage] | str | BaseMessage,
               return_dict: bool = True) -> Dict[Any, Any]:
    response = llm.invoke(input)
    state['all_messages'] += (input + [response]) if isinstance(input, List) else [input]
    if return_dict:
        response = message_to_dict(response)
    return response


async def llm_ainvoke(state: MessagesState, llm: BaseChatModel, input: List[BaseMessage] | str | BaseMessage,
                      return_dict: bool = True) -> Dict[Any, Any]:
    response = await llm.ainvoke(input)
    state['all_messages'] += (input + [response]) if isinstance(input, List) else [input]
    if return_dict:
        response = message_to_dict(response)
    return response


# 示例使用
if __name__ == "__main__":
    try:
        # 测试不同类型的LLM初始化
        llm_openai = get_llm("openai")
        # llm_qwen = get_llm("qwen")

        # 测试无效类型
        llm_invalid = get_llm("invalid_type")
    except LLMInitializationError as e:
        logger.error(f"程序终止: {str(e)}")
