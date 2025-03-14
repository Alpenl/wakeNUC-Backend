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
