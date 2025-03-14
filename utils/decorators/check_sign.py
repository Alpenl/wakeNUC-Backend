import hashlib
import logging
import time
from functools import wraps
from urllib.parse import quote

from flask import request

from utils.exceptions import custom_abort


def check_sign(check_args: set):
    """ 校验参数签名，sign 参数不存在直接失败，
    request.path 也将参与 sign 计算
    
    该装饰器用于验证API请求的合法性，防止请求被篡改或伪造。
    工作原理：
    1. 检查必要参数是否存在（sign、ts、key）
    2. 验证请求时间戳是否过期
    3. 根据请求路径和参数重新计算签名
    4. 比对计算的签名与请求中的签名是否一致
    
    :param check_args: 需要参与校验的参数集合
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs) -> dict:
            # 检查必要参数是否存在
            if "sign" not in request.args.keys() or "ts" not in request.args.keys() or "key" not in request.args.keys():
                # "2o" not in request.args.keys() or
                print(request.args.keys())
                logging.warning('缺少参数')
                custom_abort(-2, '请求签名校验失败')
                
            # 检查请求时间戳是否过期（5分钟有效期）
            if int(request.args["ts"]) + 3e5 < int(time.time() * 1000):
                logging.warning('{} 参数签名过期'.format(request.args['key']))
                custom_abort(-2, '参数签名过期')
                
            # 构建需要参与签名计算的参数列表
            # 取出ts和key并放进参数列表
            need_check_args = check_args.union({'ts', 'key'})
            arg_list = []
            for k in sorted(dict(request.args)):
                if k in need_check_args:
                    # 对参数值进行URL编码，保留特定字符
                    arg_list.append(k + "=" + quote(request.args[k], safe="~()*!.\'"))
                    
            # 构建签名字符串：请求路径 + 参数列表
            # 请求路径与ts和key的md5加密
            url_args = quote(request.path) + "&".join(arg_list)
            # print(url_args)
            # print(hashlib.md5((url_args + app_secret).encode("utf-8")).hexdigest())
            
            # 计算签名并与请求中的签名比对
            if request.args["sign"] != hashlib.md5((url_args + 'app_secret').encode("utf-8")).hexdigest():
                logging.warning('{} 请求签名校验失败'.format(request.args['key']))
                custom_abort(-2, '请求签名校验失败')
                
            # 签名验证通过，执行被装饰的函数
            return f(*args, **kwargs)

        return decorated_function

    return decorator
