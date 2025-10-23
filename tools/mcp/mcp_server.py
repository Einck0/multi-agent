import asyncio
import json
import logging
from os import path

from langchain_mcp_adapters.client import MultiServerMCPClient

from utils.tools import tools_list_to_dict

logger = logging.getLogger(__name__)

async def mcp_to_tools(client):
    """
    Converts MCP (Modular Configuration Protocol) data to a format compatible with tools.

    This function processes data formatted in MCP and transforms it into a structure or
    format that can be utilized by a set of predefined tools. It ensures compatibility
    and may adjust, map, or translate the data according to the requirements of those
    tools.

    :param mcp_data: Data formatted in MCP to be converted for tools
    :type mcp_data: any
    :return: The converted data structured for tool compatibility
    :rtype: any
    """
    tools = await client.get_tools()
    return tools

def get_all_mcp():
    """
    Retrieve a list of all tools available.

    This function performs an operation that retrieves a comprehensive list of
    tools present. The exact mechanism of retrieval may vary based on
    implementation, such as fetching from a database, parsing from a file, or
    hardcoding a set of tools.

    :return: A list containing the names or descriptions of all tools.
    :rtype: list
    """
    json_path = path.join('tools','mcp','all_mcp_config.json')
    try:
        with open(json_path,'r')as json_file:
            mcp_servers = json.load(json_file)


    except FileNotFoundError:
        logger.error('{} Not Found'.format(json_path))
        raise FileNotFoundError('{} Not Found'.format(json_path))
        return []

    except json.decoder.JSONDecodeError:
        logger.error('No MCP server config file found at {}'.format(json_path))
        raise FileNotFoundError('No MCP server config file found at {}'.format(json_path))
        return []

    vaild_mcp_servers = vaildate_mcp_json(mcp_servers)
    client = MultiServerMCPClient(vaild_mcp_servers)
    return client


async def get_all_tools():
    mcp_client = get_all_mcp()
    tools = await mcp_to_tools(mcp_client)
    return tools



def vaildate_mcp_json(mcp_config):
    """
        pass
    """
    vaild_mcp_json = {}
    try:
        if isinstance(mcp_config, str):
            if not mcp_config.strip().startswith(
                    "{"
            ) or not mcp_config.strip().endswith("}"):
                logger.error("JSON must start and end with curly braces ({}).")
                # print('Correct format: `{ "tool_name": { ... } }`')
            else:
                # Parse JSON
                parsed_tool = json.loads(mcp_config)
        else:
            parsed_tool = mcp_config

            # Check if it's in mcpServers format and process accordingly
            if "mcpServers" in parsed_tool:
                # Move contents of mcpServers to top level
                parsed_tool = parsed_tool["mcpServers"]
                logger.info(
                    "'mcpServers' format detected. Converting automatically."
                )

            # Check number of tools entered
            if len(parsed_tool) == 0:
                logger.error("Please enter at least one tool.")
            else:
                # Process all tools
                success_tools = []
                for tool_name, tool_config in parsed_tool.items():
                    # Check URL field and set transport
                    if "url" in tool_config:
                        # Set transport to "sse" if URL exists
                        tool_config["transport"] = "sse"
                        logger.info(
                            f"URL detected in '{tool_name}' tool, setting transport to 'sse'."
                        )
                    elif "transport" not in tool_config:
                        # Set default "stdio" if URL doesn't exist and transport isn't specified
                        tool_config["transport"] = "stdio"

                    # Check required fields
                    if (
                            "command" not in tool_config
                            and "url" not in tool_config
                    ):
                        logger.error(
                            f"'{tool_name}' tool configuration requires either 'command' or 'url' field."
                        )
                    elif "command" in tool_config and "args" not in tool_config:
                        logger.error(
                            f"'{tool_name}' tool configuration requires 'args' field."
                        )
                    elif "command" in tool_config and not isinstance(
                            tool_config["args"], list
                    ):
                        logger.error(
                            f"'args' field in '{tool_name}' tool must be an array ([]) format."
                        )
                    else:
                        vaild_mcp_json[tool_name] = tool_config
                        success_tools.append(tool_name)

                # Success message
                if success_tools:
                    if len(success_tools) == 1:
                        logger.info(
                            f"{success_tools[0]} tool has been added."
                        )
                    else:
                        tool_names = ", ".join(success_tools)
                        logger.info(
                            f"Total {len(success_tools)} tools ({tool_names}) have been added."
                        )
                return vaild_mcp_json

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        # print(
        #     f"""
        # **How to fix**:
        # 1. Check that your JSON format is correct.
        # 2. All keys must be wrapped in double quotes (").
        # 3. String values must also be wrapped in double quotes (").
        # 4. When using double quotes within a string, they must be escaped (\\").
        # """
        # )
    except Exception as e:
        logger.error(f"Error occurred: {e}")

async def get_all_tools_dict():
    tools = await get_all_tools()
    tools_dict = tools_list_to_dict(tools)
    return tools_dict

async def main():
    tools = await get_all_tools_dict()
    result = await tools["send_message"].ainvoke({"message":"hello"})
    print(result)

if __name__ == '__main__':
    asyncio.run(main())