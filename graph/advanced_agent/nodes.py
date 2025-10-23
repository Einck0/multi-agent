import json
import logging

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from graph.advanced_agent.prompts import *
from graph.advanced_agent.state import State
from tools.mcp.mcp_server import get_all_tools, get_all_tools_dict

load_dotenv()
# llm = ChatOpenAI(model="gemini-2.5-flash", temperature=0.0)
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.0)

format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, # 设置根logger的级别
                    format=format,
                    handlers=[logging.StreamHandler()]) # 添加StreamHandler
# 也可以像之前那样，获取一个以当前模块命名的logger，但它的处理器和格式器会由basicConfig共享
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
    messages = [SystemMessage(content=PLAN_SYSTEM_PROMPT), HumanMessage(content=PLAN_CREATE_PROMPT.format(user_message = state['user_message']))]
    response = llm.invoke(messages)
    response = response.model_dump_json(indent=4, exclude_none=True)
    response = json.loads(response)
    plan = json.loads(extract_json(extract_answer(response['content'])))
    state['messages'] += [AIMessage(content=json.dumps(plan, ensure_ascii=False))]
    state['plan'] = plan
    return {'plan': plan}

def update_planner_node(state: State):
    logger.info("***正在运行Update Planner node***")
    plan = state['plan']
    goal = plan['goal']
    state['messages'].extend([SystemMessage(content=PLAN_SYSTEM_PROMPT), HumanMessage(content=UPDATE_PLAN_PROMPT.format(plan = plan, goal=goal))])
    messages = state['messages']
    while True:
        try:
            response = llm.invoke(messages)
            response = response.model_dump_json(indent=4, exclude_none=True)
            response = json.loads(response)
            plan = json.loads(extract_json(extract_answer(response['content'])))
            state['messages']+=[AIMessage(content=json.dumps(plan, ensure_ascii=False))]
            return {'plan': plan}
        except Exception as e:
            messages += [HumanMessage(content=f"json格式错误:{e}")]


async def execute_node(state: State):
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

    tools = await get_all_tools()
    tools_dict = await get_all_tools_dict()
    tool_message = None
    response_content = None
    while True:
        response = await llm.bind_tools(tools).ainvoke(messages)
        response = response.model_dump_json(indent=4, exclude_none=True)
        response = json.loads(response)
        response_content = extract_answer(response['content'])
        if response['tool_calls']:
            for tool_call in response['tool_calls']:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_result = await tools_dict[tool_name].ainvoke(tool_args)
                logger.info(f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}")
                messages += [AIMessage(content=response_content,tool_calls=response['tool_calls'])]
                tool_message = [ToolMessage(content=f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}",
                                name=tool_name,tool_call_id=tool_call['id'])]
                messages += tool_message

        elif '<tool_call>' in response['content']:
            tool_call = response['content'].split('<tool_call>')[-1].split('</tool_call>')[0].strip()

            tool_call = json.loads(tool_call)

            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_result = await tools_dict[tool_name].ainvoke(tool_args)
            logger.info(f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}")
            messages += [AIMessage(content=extract_answer(response['content']))]
            messages += [HumanMessage(content=f"tool_result:{tool_result}")]
        else:
            break

    logger.info(f"当前STEP执行总结:{response_content}")
    state['messages'].append(response)
    state['observations'].append(response_content)
    return {'plan': plan}


async def report_node(state: State):
    """Report node that writes a final report."""
    logger.info("***正在运行report_node***")
    
    observations = state.get("observations")
    messages = observations + [HumanMessage(content=REPORT_SYSTEM_PROMPT)]
    tools = await get_all_tools()
    tools_dict = await get_all_tools_dict()
    while True:
        response = llm.bind_tools(tools).invoke(messages)
        response = response.model_dump_json(indent=4, exclude_none=True)
        response = json.loads(response)
        if response['tool_calls']:
            for tool_call in response['tool_calls']:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_result = await tools_dict[tool_name].ainvoke(tool_args)
                logger.info(f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}")
                messages += [AIMessage(content=extract_answer(response['content']),tool_calls=response['tool_calls'])]
                messages += [ToolMessage(content=f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}",
                                name=tool_name,tool_call_id=tool_call['id'])]
                
        elif '<tool_call>' in response['content']:
            tool_call = response['content'].split('<tool_call>')[-1].split('</tool_call>')[0].strip()
            
            tool_call = json.loads(tool_call)
            
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_result = await tools_dict[tool_name].ainvoke(tool_args)
            logger.info(f"tool_name:{tool_name},tool_args:{tool_args}\ntool_result:{tool_result}")
            messages += [AIMessage(content=extract_answer(response['content']))]
            messages += [HumanMessage(content=f"tool_result:{tool_result}")] 
        else:
            break
            
    return {"final_report": response['content']}


def should_exec_node(state: State):
    """Check if the node should execute."""
    pass

def exec_tools(tools):

    pass