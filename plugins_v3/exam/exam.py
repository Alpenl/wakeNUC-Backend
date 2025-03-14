from flask import request

from global_config import post_data as glo_data
from plugins_v3._login.login import login
from utils.decorators.cache import cache
from utils.decorators.check_sign import check_sign
from utils.decorators.request_limit import request_limit
from utils.session import session
from . import api, config


@api.route("/exam", methods=["GET"])
@check_sign({'name', 'passwd'})
@request_limit()
@cache({'name'}, 300)
def handle_exam():
    """
    获取学生考试信息接口
    
    请求参数:
    - name: 学号
    - passwd: 密码
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 考试信息列表，包含考试类型、课程名称、考试地点和时间
    """
    name = request.args.get('name', '')
    passwd = request.args.get('passwd', '')
    cookies = login(name, passwd)
    post_data = {
        'xnm': glo_data['xnm'],
        'xqm': glo_data['xqm'],
        'queryModel.showCount': 500
    }
    items = session.post(config.exam_url, data=post_data, cookies=cookies).json()
    exam_items = []
    for item in items["items"]:
        exam_items.append({
            'type': item['ksmc'],
            'college': item['jxbmc'],
            'location': item['cdmc'],
            'time': item['kssj']
        })
    return {
        'code': 0,
        'data': exam_items
    }
