import asyncio
import json
import logging

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from graph.advanced_agent.prompts import *
from graph.advanced_agent.state import State
from tools.mcp.mcp_server import get_all_tools, get_all_tools_dict
from utils.llm import llm_invoke, llm_ainvoke
from utils.tools import message_to_dict

load_dotenv()
# llm = ChatOpenAI(model="gemini-2.5-flash", temperature=0.0)
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.0)
tools = asyncio.run(get_all_tools())
tools_dict = asyncio.run(get_all_tools_dict())
tools_info = str(tools)
logger = logging.getLogger(__name__)

def extract_json(text):
    if '```json' not in text:
        return text
    text = text.split('```json')[1].split('```')[0].strip()
    return text

def extract_answer(text):
    if '</think>' in text:
        answer = text.split("</think>")[-1]
        return answer.strip()
    
    return text


def create_planner_node(state: State):
    logger.info("***正在运行Create Planner node***")
    messages = [SystemMessage(content=PLAN_SYSTEM_PROMPT), HumanMessage(
        content=PLAN_CREATE_PROMPT.format(user_message=state['user_message'], tools_info=tools_info))]
    response = llm_invoke(state, llm, messages)
    state['observations'] += [str(response)]
    plan = json.loads(extract_json(extract_answer(response['content'])))
    return {'plan': plan}

def update_planner_node(state: State):
    logger.info("***正在运行Update Planner node***")
    plan = state['plan']
    goal = plan['goal']
    messages = state['observations']
    messages.extend([SystemMessage(content=PLAN_SYSTEM_PROMPT),
                     HumanMessage(content=UPDATE_PLAN_PROMPT.format(plan=plan, goal=goal))])
    while True:
        try:
            response = llm_invoke(state, llm, messages)
            plan = json.loads(extract_json(extract_answer(response['content'])))
            state['messages']+=[AIMessage(content=json.dumps(plan, ensure_ascii=False))]
            return {'plan': plan}
        except Exception as e:
            messages += [HumanMessage(content=f"json格式错误:{e}")]


def execute_node(state: State):
    logger.info("***正在运行execute_node***")
  
    plan = state['plan']
    steps = plan['steps']
    current_step = None
    current_step_index = 0
    
    # 获取第一个未完成STEP
    for i, step in enumerate(steps):
        status = step['status']
        if status == 'pending':
            current_step = step
            current_step_index = i
            break
        
    logger.info(f"当前执行STEP:{current_step}")
    
    messages = state['observations'] + [SystemMessage(content=EXECUTE_SYSTEM_PROMPT),
                                        HumanMessage(content=EXECUTION_PROMPT.format(user_message=state['user_message'],
                                        step=current_step['description']))]

    # tools = await get_all_tools()
    # tools_dict = await get_all_tools_dict()

    tool_message = None
    response_content = None
    while True:
        response = asyncio.run(llm_ainvoke(state, llm.bind_tools(tools), messages, False))
        state['observations'] += [response]
        response = message_to_dict(response)
        response_content = extract_answer(response['content'])
        if response['tool_calls']:
            for tool_call in response['tool_calls']:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_result = asyncio.run(tools_dict[tool_name].ainvoke(tool_args))
                logger.info(f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}")
                ai_message = AIMessage(content=response_content, tool_calls=response['tool_calls'])
                yield {'messages': [ai_message]}
                tool_message = ToolMessage(
                    content=f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}",
                    name=tool_name, tool_call_id=tool_call['id'])
                messages += [ai_message, tool_message]
                state['observations'] += [tool_message]
                yield {'messages': [tool_message]}

        elif '<tool_call>' in response['content']:
            tool_call = response['content'].split('<tool_call>')[-1].split('</tool_call>')[0].strip()

            tool_call = json.loads(tool_call)

            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_result = asyncio.run(tools_dict[tool_name].ainvoke(tool_args))
            logger.info(f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}")
            messages += [AIMessage(content=extract_answer(response['content']))]
            messages += [HumanMessage(content=f"tool_result:{tool_result}")]
        else:
            break

    logger.info(f"当前STEP执行总结:{response_content}")

    return


def report_node(state: State):
    """Report node that writes a final report."""
    logger.info("***正在运行report_node***")
    
    observations = state.get("observations")
    messages = observations + [HumanMessage(content=REPORT_SYSTEM_PROMPT)]
    response = llm_invoke(state, llm, messages)
    response = AIMessage(content=response['content'])
    # state['messages'] += [AIMessage(content=response["content"])]
    # state['final_report'] += [AIMessage(content=response["content"])]
    # return state
    return {"final_report": response, "messages": [response]}
