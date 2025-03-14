from flask import request

from utils.exceptions import custom_abort
from . import api
from utils.decorators.check_sign import check_sign
from utils.session import session
from plugins_v3.physical import config
from plugins_v3._login.login import physical_login
from utils.decorators.request_limit import request_limit
from utils.decorators.cache import cache


@api.route('/physical', methods=['GET'])
@check_sign(check_args={'name', 'passwd'})  # 验证请求签名
@request_limit(5)                           # 限制请求频率，每分钟最多5次
@cache({'name'}, 300)                       # 缓存结果300秒
def physical():
    """
    获取学生体测总成绩信息
    
    查询参数:
    - name: 学号
    - passwd: 密码
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 体测成绩信息，包含各学期体测数据
    """
    # 获取请求参数
    name = request.args.get('name', type=str)
    passwd = request.args.get('passwd', type=str)
    
    # 登录体育管理系统获取Cookie
    cookies = physical_login(name, passwd)
    
    # 访问预处理页面
    session.get(url=config.pre_url, cookies=cookies)
    
    # 获取用户ID
    rs = session.post(url=config.sys_url, cookies=cookies)
    userid = rs.json()['data'][0]['sysUser']['id']
    
    # 构建请求数据
    post_data = {
        'userId': userid
    }
    
    # 请求体测总成绩数据
    rq = session.post(url=config.index_url, data=post_data, cookies=cookies).json()
    if rq['returnCode'] != '200':
        custom_abort(-1, rq['returnMsg'])
    
    # 返回体测成绩数据
    return {
        'code': 0,
        'data': rq['data']
    }


@api.route('/physical/details', methods=['GET'])
@check_sign(check_args={'meaScoreId'})  # 验证请求签名
@request_limit(10)                      # 限制请求频率，每分钟最多10次
@cache({'meaScoreId'}, 300)             # 缓存结果300秒
def physical_details():
    """
    获取体测成绩详细信息
    
    查询参数:
    - meaScoreId: 体测成绩ID
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 体测成绩详细信息，包含各项测试数据
    """
    # 获取请求参数
    grade_id = request.args.get('meaScoreId', type=str)
    
    # 构建请求数据
    post_data = {
        'meaScoreId': grade_id
    }
    
    # 请求体测详细成绩数据
    rq = session.post(config.details_url, data=post_data).json()
    if rq['returnCode'] != '200':
        custom_abort(-1, rq['returnMsg'])
    
    # 返回体测详细成绩数据
    return {
        'code': 0,
        'data': rq['data']
    }



