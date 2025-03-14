from models.notice import Notice
from utils.decorators.cache import cache
from . import api
from flask import request


@api.route('/notices', methods=['GET'])
@cache(set(), 120)  # 缓存结果120秒
def handle_notice():
    """
    获取所有通知列表，分为置顶和非置顶两类
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 通知数据对象
      - stick: 置顶通知列表
      - notStick: 非置顶通知列表
    """
    # 暂时注释掉数据库查询相关代码，之后添加相关功能时启用数据库
    # stick_notices = Notice.query.filter(Notice.is_stick == 1, Notice.is_show == 1).order_by(Notice.id_.desc()).all()
    # not_stick_notices = Notice.query.filter(Notice.is_stick == 0, Notice.is_show == 1).order_by(Notice.id_.desc()).all()
    
    # 返回空列表
    return {
        'code': 0,
        'data': {
            'stick': [],      # 置顶通知列表
            'notStick': []    # 非置顶通知列表
        }
    }


@api.route('/notices/<int:notice_id>', methods=['GET'])
@cache(set(), 120)  # 缓存结果120秒
def handle_notice_detail(notice_id: int):
    """
    获取指定通知的详细信息
    
    路径参数:
    - notice_id: 通知ID
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 通知详细信息，包含通知内容
    """
    # 暂时注释掉数据库查询相关代码
    # return {
    #     'code': 0,
    #     'data': Notice.query.get(notice_id).serialize()
    # }
    return {
        'code': 0,
        'data': {}
    }


@api.route('/notices/latest', methods=['GET'])
@cache(set(), 1800)  # 缓存结果1800秒（30分钟）
def handle_notice_latest():
    """
    获取最新的重要通知
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 最新重要通知信息，如果没有则返回空列表
    """
    # 暂时注释掉数据库查询相关代码
    # latest_notice = Notice.query.filter(Notice.is_important == 1, Notice.is_show == 1).order_by(Notice.time.desc()).first()
    
    return {
        'code': 0,
        'data': []
    }


@api.route('/notices/pop', methods=['GET'])
@cache({'type'}, 30)  # 缓存结果30秒，根据type参数区分
def handle_notice_pop():
    """
    获取弹窗通知
    
    查询参数:
    - type: 弹窗类型，可选值为'home'(首页)或'agent'(代理页)，默认为1(首页)
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 弹窗通知信息，如果没有则返回空列表
    """
    # 获取弹窗类型参数
    pop_type = request.args.get('type', 1)
    
    # 转换弹窗类型参数
    if pop_type == "home":
        pop_type = 1  # 首页弹窗
    elif pop_type == "agent":
        pop_type = 2  # 代理页弹窗
    
    # 暂时注释掉数据库查询相关代码
    # pop_notices = Notice.query.filter(Notice.is_pop == pop_type).first()
    
    return {
        'code': 0,
        'data': []
    }
