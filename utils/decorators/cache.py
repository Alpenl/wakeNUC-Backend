import hashlib
import json
import logging
from functools import wraps
from urllib.parse import unquote

from flask import request, g

from utils.redis_connections import redis_cache


def cache(cache_args: set, expire: int = 600):
    """ 缓存请求，若命中缓存直接返回
    
    该装饰器用于缓存API响应结果，减少重复请求对后端系统的压力。
    工作原理：
    1. 根据指定的请求参数生成缓存键
    2. 检查Redis中是否存在对应的缓存
    3. 如果缓存存在，直接返回缓存结果
    4. 如果缓存不存在，执行原函数并缓存结果

    :param cache_args: 根据 cache_args 生成缓存唯一缓存 id，这是一个参数名集合
    :param expire: 缓存过期时间（秒）,默认 600 秒
    """

    def decorator(f):
        @wraps(f)
        # 保持原有name
        def decorated_function(*args, **kwargs) -> dict:
            # 构建缓存键
            arg_list = []
            for k in sorted(dict(request.args)):
                # 判断参数是否是需要缓存的key
                if k in cache_args:
                    # 将过滤的请求参数逐个取出
                    arg_list.append(k + "=" + request.args.get(k))
            if arg_list:
                # 拼接url
                cache_key = request.path + '?' + '&'.join(arg_list)
            else:
                cache_key = request.path
            # md5加密生成缓存键
            cache_key_md5 = hashlib.md5(cache_key.encode()).hexdigest()
            # 从Redis取出缓存
            cached = redis_cache.get(cache_key_md5)
            if cached:
                # 缓存命中，设置标记并返回缓存结果
                g.values['cached'] = True
                g.values['code'] = 0
                logging.info("命中缓存 %s", unquote(cache_key))
                return json.loads(cached)
            else:
                # 缓存未命中，执行原函数
                res: dict = f(*args, **kwargs)
                g.values['code'] = res.get('code', -1)
                # 只有成功的响应才会被缓存
                if res.get('code', -1) == 0:
                    # 设置缓存，并指定过期时间
                    redis_cache.set(cache_key_md5, json.dumps(res), ex=expire)
                    logging.info("缓存 %s", unquote(cache_key))
                return res

        return decorated_function

    return decorator
