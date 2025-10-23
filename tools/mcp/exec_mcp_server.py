import os
import subprocess

from fastmcp import FastMCP

mcp = FastMCP("exec-mcp-server")


@mcp.tool
def create_file(file_name: str, file_contents: str) -> dict:
    """
    在工作区指定路径创建一个新文件，并写入提供的内容。

    Args:
        file_name (str): 要创建的文件名（只能是相对路径，必须在AI-generated下，例如 "AI-generated/my_file.txt"）。
        file_contents (str): 要写入文件的内容。

    Returns:
        dict: 包含操作结果的消息或错误。
    """
    try:
        # 确保文件路径是相对于当前工作目录的
        file_path = os.path.join(os.getcwd(), file_name)

        # 递归创建父目录，如果它们不存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(file_contents)

        return {
            "message": f"成功在 '{file_path}' 创建了文件。"
        }
    except Exception as e:
        return {
            "error": f"创建文件 '{file_name}' 失败: {str(e)}"
        }


@mcp.tool
def str_replace(file_name: str, old_str: str, new_str: str, all_occurrences: bool = False) -> dict:
    """
    替换文件中指定文本。

    Args:
        file_name (str): 目标文件名。
        old_str (str): 要被替换的文本。
        new_str (str): 替换文本。
        all_occurrences (bool): 如果为 True，替换所有匹配项；否则只替换第一次匹配。默认为 False。

    Returns:
        dict: 包含操作结果的消息或错误。
    """
    try:
        file_path = os.path.join(os.getcwd(), file_name)

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {"error": f"文件 '{file_name}' 不存在。"}

        with open(file_path, "r", encoding='utf-8') as file:
            content = file.read()

        replace_count = -1 if all_occurrences else 1
        new_content = content.replace(old_str, new_str, replace_count)

        # 如果内容没有改变，说明没有找到需要替换的字符串
        if new_content == content:
            return {
                "message": f"在文件 '{file_name}' 中未找到 '{old_str}'。" if not all_occurrences else f"在文件 '{file_name}' 中未找到 '{old_str}'，或已全部替换。"}  # 这里的提示可以根据实际需求调整

        with open(file_path, "w", encoding='utf-8') as file:
            file.write(new_content)

        action_word = "所有匹配项" if all_occurrences else "第一次匹配项"
        return {"message": f"在文件 '{file_name}' 中成功将 '{old_str}' 的 {action_word} 替换为 '{new_str}'。"}
    except Exception as e:
        return {"error": f"替换文件 '{file_name}' 中的文本失败: {str(e)}。"}


@mcp.tool
def send_message(message: str) -> str:
    """
    向用户发送一条消息。此工具通常用于向用户报告当前状态、询问问题或提供最终结果。

    Args:
        message (str): 要发送给用户的文本消息。

    Returns:
        str: 返回接收到的消息内容。
    """
    return message


@mcp.tool
def shell_exec(command: str) -> dict:
    """
    在指定的 shell 会话中执行命令。

    参数:
        command (str): 要执行的 shell 命令。

    返回:
        dict: 包含以下字段：
            - message (dict): 包含命令的 `stdout` 和 `stderr`。
                - stdout (str): 命令的标准输出。
                - stderr (str): 命令的标准错误。
            - error (dict, 可选): 如果命令执行本身失败，此字段会存在，包含错误信息。
    """
    try:
        # 执行命令
        result = subprocess.run(
            command,
            shell=True,  # 允许命令作为 shell 命令执行
            cwd=os.getcwd(),  # 设置当前工作目录为 MCP 的工作目录
            capture_output=True,  # 捕获标准输出和标准错误
            text=True,  # 将 stdout 和 stderr 解码为文本
            check=False  # 不在非零退出码时引发 CalledProcessError，而是在结果中报告
        )

        # 无论命令成功还是失败，都返回其 stdout 和 stderr
        return {
            "message": {
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }

    except Exception as e:
        # 只有当 subprocess.run 本身抛出异常时（例如，命令字符串格式错误），才会捕获到这里
        return {
            "error": {
                "stderr": f"执行 shell 命令时发生意外错误: {str(e)}"
            },
            "message": {  # 即使发生意外错误，也提供空的 stdout/stderr，保持返回格式一致
                "stdout": "",
                "stderr": f"执行 shell 命令时发生意外错误: {str(e)}"
            }
        }


if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=9000)
