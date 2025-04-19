import os

# 微信小程序配置
# 用于参数校验和获取openid
# 小程序appid
app_id = 'wx1955353b7aabde0e'
# 小程序的appsecret
app_secret = 'abe345b85cca2671e9b11684167de8ad'

# 测试账号配置
# 测试学号密码和全局账号
# 学号
NAME = ""
# 密码
PASSWD = ""

# 通知配置
# 个人手机号码(本地运行可不配置)
PHONE = [""]

# 用户管理
# 黑名单用户
blacklist = ['']  # 存储被拉黑用户的openid列表

# 网络配置
# 代理服务器(本地运行可不配置)
proxyIp = os.getenv('PROXY_IP')  # socks代理地址
# 是否启用代理
enableProxy = os.getenv('ENABLE_PROXY', 'true').lower() == 'true'

# 多代理配置
# 代理列表，格式为 [{"url": "地址:端口", "type": "代理类型", "username": "用户名(可选)", "password": "密码(可选)"}]
# 代理类型支持: socks5, http, https
proxy_list = [
    # 默认从环境变量中读取的代理
    {"url": proxyIp, "type": "socks5"} if proxyIp else None
]

# 添加额外的代理
additional_proxies = [
    # 可以在此添加更多代理
    # {"url": "192.168.1.100:1080", "type": "socks5"},
    # {"url": "proxy.example.com:8080", "type": "http", "username": "user", "password": "pass"},
]

# 移除None值并合并代理列表
proxy_list = [p for p in proxy_list if p] + additional_proxies

# 代理轮询策略: 'round_robin'(默认轮询), 'random'(随机选择)
proxy_rotation_policy = 'round_robin'

# 代理请求超时时间(秒)
proxy_request_timeout = 10

# 代理失败后重试延迟(秒)
proxy_retry_delay = 0.5

# redis配置
# redis = {
#     # ip地址
#     'host': 'localhost',
#     # 密码(没有可不配置)
#     # 'username': 'default',
#     'password': '',
#     'port': 6379
# }

# 数据库配置
# redis配置
redis = {
    # ip地址
    'host': os.getenv('REDIS_HOST'),
    # 密码(没有可不配置)
    'username': os.getenv('REDIS_USERNAME'),
    'password': os.getenv('REDIS_PASSWORD'),
    'port': int(os.getenv('REDIS_PORT')) if os.getenv('REDIS_PORT') else None
}

# # mysql配置(端口3306)已经移除mysql,但是保留了配置方便扩展
# mysql = {
#     # ip地址
#     'host': '',
#     # 账号
#     'user': 'root',
#     # 密码
#     'password': 'root'
# }


# 学期配置
# 课程查询SQL语句
# sql_one = "SELECT * FROM `课程-2023-1` WHERE `教师` like %s or `课程名` like %s "
# sql_two = "SELECT * FROM `课程-2023-1` WHERE `班级` like %s "

# 当前学期配置
post_data = {
    'xnm': '2024',  # 学年
    'xqm': '12',    # 学期（3表示第一学期，12表示第二学期）
    'xnmc': '2023-2024',  # 学年名称
}

# 可选学期列表配置
term_list = [
    {
        'name': '2022-1',  # 学期名称
        'postData': {
            'xnm': '2022',  # 学年
            'xqm': '3'      # 学期（第一学期）
        }
    },
    {
        'name': '2022-2',
        'postData': {
            'xnm': '2022',
            'xqm': '12'     # 学期（第二学期）
        }
    },
    {
        'name': '2023-1（当前学期）',
        'postData': {
            'xnm': '2023',
            'xqm': '3'
        }
    }
]
