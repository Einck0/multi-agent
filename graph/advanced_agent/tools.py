from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient


# 获取工具列表 提供给第三方调用
async def get_tools():

    # MCP Server工具 高德地图
    client = MultiServerMCPClient({
        # 高德地图MCP Server
        "amap-amap-sse": {
            "url": "https://mcp.amap.com/sse?key=8489a1e2b419d5e996be19d64a65e50bb0757",
            "transport": "sse",
        }
    })
    # 从MCP Server中获取可提供使用的全部工具
    amap_tools = await client.get_tools()
    # 为工具添加人工审查
    tools = [amap_tools]

    # 返回工具列表
    return tools

# 自定义工具 计算两个数的乘积的工具
@tool("multiply", description="计算两个数的乘积的工具")
async def multiply(a: float, b: float) -> float:
    """
   支持计算两个数的乘积的工具

    Args:
        a: 参数1
        b: 参数2

    Returns:
        工具的调用结果
    """
    result = a * b
    return f"{a}乘以{b}等于{result}。"
