# 导入Flask蓝图，用于模块化路由管理
from flask import Blueprint

# 创建课表模块的蓝图，设置名称和URL前缀
# 'timetable_v3'是蓝图名称，用于内部标识
# url_prefix='/v3'表示该模块下所有路由都以'/v3'开头
api = Blueprint('timetable_v3', __name__, url_prefix='/v3')

# 导入模块内的功能文件，使其中定义的路由注册到蓝图中
from .timetable import *  # 导入课表查询相关功能
