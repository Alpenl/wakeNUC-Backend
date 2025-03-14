from flask import request
from plugins_v3._login.login import login
from utils.decorators.check_sign import check_sign
from utils.decorators.request_limit import request_limit
from utils.session import session
from . import api, config
from utils.decorators.cache import cache
from lxml import etree


@api.route('/studies', methods=['GET'])
@check_sign({'name', 'passwd'})  # 验证请求签名
@request_limit()                 # 限制请求频率
@cache({'name'}, 180)            # 缓存结果180秒
def handle_studies():
    """
    获取学生学习情况统计信息
    
    请求参数:
    - name: 学号
    - passwd: 密码
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 学习情况列表，包含课程类型、GPA和学分信息
    """
    # 获取请求参数
    name = request.args.get('name', type=str)
    passwd = request.args.get('passwd', type=str)
    
    # 登录获取Cookie
    cookies = login(name, passwd)
    
    # 构建请求数据
    post_data = {
        '_search': 'false',
    }
    
    studies_list = []
    # 获取课程类型统计数据
    studies = session.post(config.studies_url, post_data, cookies=cookies).json()
    # 获取所有课程的平均GPA
    all_studies = get_all_studies(cookies)
    
    # 处理每种课程类型的数据
    studies = studies['items']
    for study in studies:
        one_list = {
            'name': study['kcxzmc'],      # 课程性质名称
            'gpa': study.get('gpa', ''),  # 该类课程的GPA
            'xf': study['hdxf']           # 获得学分
        }
        studies_list.append(one_list)
    
    # 添加所有课程的平均GPA
    studies_list.append({'name': '所有课程平均GPA', 'gpa': all_studies})
    
    # 返回学习情况数据
    return {
        'code': 0,
        'data': studies_list
    }


def get_all_studies(cookies):
    """
    获取所有课程的平均GPA
    
    参数:
    - cookies: 登录后的Cookie
    
    返回:
    - 所有课程的平均GPA值
    """
    # 请求获取所有课程GPA的页面
    rq = session.get(url=config.all_studies_url, cookies=cookies).content.decode()
    # 解析HTML获取GPA值
    tree = etree.HTML(rq)
    all_studies = tree.xpath('normalize-space(//*[@id="alertBox"]/font[2]/font/text())')
    return all_studies
