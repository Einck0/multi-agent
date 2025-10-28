class McpConnectError(Exception):
    """一个自定义的异常类"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)  # 调用父类的构造函数
