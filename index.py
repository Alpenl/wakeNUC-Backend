import gevent.monkey
# 通过对 Python 标准库代码进行 monkey patch 可以使得原来禁止在非主线程下使用的一些函数和模块变为可以在子线程中正常工作，
# 位置不能动,否则会递归调用
gevent.monkey.patch_all()

# from global_config import mysql as mysql_config, blacklist, proxyIp
from global_config import proxy_list, enableProxy

import os
# 环境变量代理设置移至 proxy_manager 统一管理
if enableProxy and proxy_list:
    # 找出第一个socks5代理作为全局代理
    for proxy in proxy_list:
        if proxy.get('type', '').lower() == 'socks5' and proxy.get('url'):
            # 设置全局代理，用于访问校内网络资源
            os.environ["http_proxy"] = "socks5://" + proxy['url']
            os.environ["https_proxy"] = "socks5://" + proxy['url']
            break
else:
    # 如果禁用代理或代理列表为空，则清除环境变量中的代理设置
    if "http_proxy" in os.environ:
        del os.environ["http_proxy"]
    if "https_proxy" in os.environ:
        del os.environ["https_proxy"]

import requests
import json
from models.sqlalchemy_db import db
import logging
import traceback
from os import path
import flask_compress
from flask import Flask, request, Response, g
from gevent.pywsgi import WSGIServer
from startup import load_task, load_plugin
from utils.gol import global_values
from utils.logger import root_logger
from utils.scheduler import scheduler
from utils.exceptions import CustomHTTPException
import signal
import sys

# 初始化一个新的 Flask 应用程序
app = Flask(__name__)
# 注册了一个用于自动压缩响应的扩展，减少网络传输数据量
flask_compress.Compress(app)

# 设置临时的SQLite内存数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # 使用SQLite内存数据库作为临时配置，之后若使用MySQL数据库，将此配置注释后打开mysql配置

# 绑定数据库配置（MySQL配置暂时注释）
# app.config['SQLALCHEMY_BINDS'] = {
#     'nuc-info': 'mysql+pymysql://{}:{}@{}:3306/nuc_info'
#     .format(mysql_config['user'], mysql_config['password'], mysql_config['host'])
# }

# 将 SQLAlchemy 对象初始化为一个 Flask 扩展，并将其注册到 Flask 实例中的常见方法。
# 通过这种方式，我们可以在应用程序组件之间轻松地共享 SQLAlchemy 的实例对象，并统一管理和自动更新数据库模型和连接池等资源。
db.init_app(app)

# 在每个请求之前初始化g.values
@app.before_request
def before_request():
    g.values = {'code': 0}

# 添加根路由处理
@app.route('/')
def index():
    return {
        'code': 0,
        'message': 'API服务正常运行中'
    }

# 自定义HTTP异常处理器
@app.errorhandler(CustomHTTPException)
def on_custom_http_exception(e: CustomHTTPException):
    # 将错误码存储到全局变量中
    g.values['code'] = e.code
    return {
        'code': e.code,
        'message': e.message
    }


# 全局异常处理器
@app.errorhandler(Exception)
def on_sever_error(e):
    # 处理连接错误（通常是VPN或代理问题）
    if isinstance(e, requests.exceptions.ConnectionError):
        g.values['code'] = -1
        return {
            'code': -1,
            'message': 'VPN通道已关闭!'
        }
    # 处理URL格式错误
    if isinstance(e, requests.exceptions.MissingSchema):
        g.values['code'] = -1
        logging.error('教务系统异常!')
        return {
            'code': -1,
            'message': '教务系统开小差了，请重试!'
        }
    # 处理JSON解析错误
    if isinstance(e, json.decoder.JSONDecodeError):
        g.values['code'] = -1
        logging.error('JSONDecodeError异常!')
        return {
            'code': -1,
            'message': '请稍后再试!'
        }
    # 处理其他未知异常
    logging.exception(traceback.format_exc())
    logging.error("服务器异常!")
    g.values['code'] = -1
    return {
        'code': -1,
        'message': '服务器开小差了~'
    }

# 应用初始化函数
def initializer():
    # 设置代理状态为正常
    global_values.set_value("proxy_status_ok", True)
    # 加载plugins_v3下所有python文件
    plugins = load_plugin.load_plugins(
        # 拼接出绝对路径
        path.join(path.dirname(__file__), 'plugins_v3'),
        # 重命名后的文件夹名
        'plugins_v3'
    )
    # 注册所有插件到Flask应用
    for i in plugins:
        # 将它们注册到 Flask 实例对象中，以便应用程序能够识别和使用这些插件
        app.register_blueprint(i.api)
        # print(i.api)
    # 加载自定义定时任务
    load_task.load_tasks(
        path.join(path.dirname(__file__), 'tasks'),
        'tasks')
    # 启动定时任务调度器
    scheduler.start()



def signal_handler(signum, frame):
    """处理退出信号"""
    logging.info('接收到退出信号，正在关闭服务器...')
    http_server.stop()
    sys.exit(0)

# 应用入口点
if __name__ == '__main__':
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化应用
    initializer()
    # 使用gevent的WSGIServer启动应用，提供高并发支持
    http_server = WSGIServer(('0.0.0.0', 8080), app, log=root_logger, error_log=root_logger)
    logging.info('服务器启动在 http://0.0.0.0:8080')
    http_server.serve_forever()
