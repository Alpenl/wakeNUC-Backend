class CustomHTTPException(Exception):
    """
    自定义HTTP异常类
    
    用于在API处理过程中抛出带有状态码和错误信息的异常，
    这些异常会被全局异常处理器捕获并转换为对应的HTTP响应。
    """
    def __init__(self, code: int, message: str = None):
        """
        初始化异常对象
        
        :param code: 错误状态码，通常为负数
        :param message: 错误描述信息
        """
        self.code = code
        self.message = message


# 错误码与默认错误信息的映射字典
_code_message = {
    -1: "服务器开小差了~",  # 服务器内部错误
    -2: "认证失败",        # 签名验证失败
    -3: "登录失败",        # 用户名或密码错误
    -4: "暂停服务",        # 接口已停用
    -5: "访问过快",        # 请求频率限制
    -6: "查询失败",        # 数据查询失败
    -7: "查询失败",        # 数据查询失败
    -8: "已完成",          # 操作已完成
}


def custom_abort(code: int, message: str = None):
    """
    抛出自定义HTTP异常的辅助函数
    
    使用此函数可以在任何地方中断请求处理流程，并返回指定的错误信息。
    如果未提供错误信息，将使用错误码对应的默认错误信息。
    
    :param code: 错误状态码
    :param message: 自定义错误信息，如果为None则使用默认错误信息
    :raises: CustomHTTPException
    """
    if not message:
        message = _code_message.get(code, '未知错误')
    raise CustomHTTPException(code, message)
