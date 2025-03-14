from http import cookiejar  # Python 2: import cookielib as cookiejar

import requests
from requests.adapters import HTTPAdapter

session = requests.Session()
# adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=3)
# 设置最大请求数
adapter = HTTPAdapter(max_retries=3)
session.mount('http://', adapter)
session.mount('https://', adapter)
session.timeout = 10  # 设置超时时间为10秒
# 设置代理
# session.proxies = proxies
# 禁用 SSL 证书验证
session.verify = False


# 拒绝保存任何cookies 不然多次请求会报错
class BlockAll(cookiejar.CookiePolicy):
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False


session.cookies.set_policy(BlockAll())
