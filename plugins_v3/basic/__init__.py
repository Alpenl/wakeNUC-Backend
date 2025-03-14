from flask import Blueprint

# 创建基础路由蓝图
api = Blueprint('basic', __name__)

# 导入路由模块
from . import routes