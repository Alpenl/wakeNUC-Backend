import logging
import time
from functools import wraps

from flask import request

from utils.exceptions import custom_abort
from utils.redis_connections import redis_request_limit


def request_limit(limit_per_minute: int = 10):
    """ 每分钟请求限制
    
    该装饰器用于限制API的请求频率，防止恶意请求或滥用。
    工作原理：
    1. 使用Redis列表存储用户的请求时间戳
    2. 每次请求时检查用户在过去一分钟内的请求次数
    3. 如果超过限制，则拒绝请求
    4. 如果未超过限制，则允许请求并记录时间戳
    
    :param limit_per_minute: 每分钟请求限制数，默认为10次/分钟
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs) -> dict:
            # 生成用户请求的唯一标识（用户key + 请求路径）
            user_key = request.args['key'] + request.path
            
            # 检查用户请求次数是否小于限制
            if redis_request_limit.llen(user_key) < limit_per_minute:
                # 未达到限制，记录当前请求时间
                redis_request_limit.lpush(user_key, time.time())
            else:
                # 已达到限制，检查最早的请求是否在一分钟内
                first_time = redis_request_limit.lindex(user_key, -1)
                if time.time() - float(first_time) < 60:
                    # 一分钟内请求次数超过限制，拒绝请求
                    logging.warning("{} 达到请求限制（{}次/分钟）".format(request.args['key'], limit_per_minute))
                    custom_abort(-5, '操作过频繁')
                else:
                    # 最早的请求已超过一分钟，可以接受新请求
                    # 添加新请求时间并保持列表长度为限制次数
                    redis_request_limit.lpush(user_key, time.time())
                    redis_request_limit.ltrim(user_key, 0, limit_per_minute - 1)
            
            # 设置键的过期时间为60秒，避免长期占用内存
            redis_request_limit.expire(user_key, 60)

            # 执行被装饰的函数
            return f(*args, **kwargs)

        return decorated_function

    return decorator
