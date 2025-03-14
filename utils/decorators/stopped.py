from functools import wraps

from utils.exceptions import custom_abort


def stopped(message: str = '暂停服务'):
    """ 已停止服务，直接返回
    
    该装饰器用于标记已暂停的API服务，被装饰的函数将不会执行，
    而是直接返回一个错误响应，通知用户该服务当前不可用。
    
    使用场景：
    1. 临时关闭某些功能进行维护
    2. 废弃旧接口但保留路由
    3. 应对突发情况需要紧急关闭某些服务
    
    :param message: 自定义的暂停服务提示信息，默认为"暂停服务"
    """

    def decorator(f):
        @wraps(f)
        def decorated_function():
            # 直接抛出自定义异常，中断请求处理流程
            # 错误码-4表示服务暂停
            custom_abort(-4, message)

        return decorated_function

    return decorator
