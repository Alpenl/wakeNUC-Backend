import logging

from flask import request

from plugins_v3._login.login import login
from utils.decorators.cache import cache
from utils.decorators.check_sign import check_sign
from utils.decorators.request_limit import request_limit
from utils.session import session
from utils.decorators.stopped import stopped
from . import api, config


@api.route('/grade', methods=['GET'])
@check_sign(check_args={'name', 'passwd'})
# @stopped()
@request_limit()
def handle_grade():
    """
    获取学生所有学期成绩接口
    
    请求参数:
    - name: 学号
    - passwd: 密码
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 成绩信息列表，按学期分组
    """
    # 获取请求参数
    name = request.args.get('name', type=str)
    passwd = request.args.get('passwd', type=str)
    
    # 登录获取Cookie
    cookies = login(name, passwd)
    
    # 构建请求数据，空的xnm和xqm表示查询所有学期
    post_data = {
        'xnm': '',                    # 学年，空表示所有学年
        'xqm': '',                    # 学期，空表示所有学期
        'queryModel.showCount': 1000, # 最大返回数量
        '_search': 'false'            # 是否搜索模式
    }
    
    try:
        # 请求教务系统获取成绩信息
        grade = session.post(config.grade_url, post_data, cookies=cookies).json()
    except Exception:
        # 如果请求失败，尝试重新登录并再次请求
        cookies = login(name, passwd, True)  # 强制重新登录
        grade = session.post(config.grade_url, post_data, cookies=cookies).json()
        logging.warning("捕获成绩查询异常!")
    
    # 处理返回的成绩数据，按学期分组
    grade_items = {}
    for item in grade['items']:
        # 生成学期键：学年开始年份 + 学期/2（如：2022.5表示2022-2023学年第一学期）
        dict_key = int(item['xnmmc'][:4]) + int(item['xqmmc'])/2
        if dict_key not in grade_items:
            grade_items[dict_key] = []
        
        # 添加课程成绩信息
        grade_items[dict_key].append({
            'name': item.get('kcmc', '')+'['+item.get('kcxzmc', '')+']',  # 课程名称[课程性质]
            'credit': float(item['xf']) if 'xf' in item else '',           # 学分
            'grade': item.get('bfzcj', ''),                                # 成绩
            'gradePoint': float(item['jd']) if 'jd' in item else '',       # 绩点
            'testType': item.get('kcxzmc', ''),                            # 课程类型
            'testStatus': item.get('ksxz', ''),                            # 考试状态
        })
    
    # 按学期键排序
    index = sorted(grade_items.keys())
    data = []
    
    # 将成绩数据按学期顺序整理到列表中
    for list_index in index:
        data.append(grade_items[list_index])
    
    # 计算总体绩点和必修课绩点
    g_a, g_b = 0, 0  # g_a: 总学分绩点乘积之和，g_b: 总学分之和
    g_a_, g_b_ = 0, 0  # g_a_: 必修课学分绩点乘积之和，g_b_: 必修课学分之和
    
    for item_i in data:
        a, b = 0, 0  # 当前学期的学分绩点乘积之和和学分之和
        a_, b_ = 0, 0  # 当前学期的必修课学分绩点乘积之和和学分之和
        
        for item_j in item_i:
            # 如果课程有学分和绩点，计算学分绩点乘积
            if item_j['credit'] and item_j['gradePoint']:
                t = item_j['credit'] * item_j['gradePoint']  # 学分与绩点的乘积
                a += t  # 累加到当前学期总和
                g_a += t  # 累加到所有学期总和
                b += item_j['credit']  # 累加学分
                g_b += item_j['credit']  # 累加到所有学期学分总和
                
                # 如果是必修课，单独计算必修课绩点
                if item_j['testType'] in ['必修']:
                    a_ += t  # 累加到当前学期必修课总和
                    g_a_ += t  # 累加到所有学期必修课总和
                    b_ += item_j['credit']  # 累加必修课学分
                    g_b_ += item_j['credit']  # 累加到所有学期必修课学分总和
                
                # 删除不需要返回的字段
                del item_j['testType']
                del item_j['testStatus']
        
        # 如果当前学期有课程，添加学期平均绩点信息
        if b:
            item_i.append({
                'name': '平均绩点',
                'gradePoint': round(a / b, 2),  # 计算当前学期平均绩点（四舍五入到两位小数）
                'credit': b  # 当前学期总学分
            })
        
        # 如果当前学期有必修课，添加必修课平均绩点信息
        if b_:
            item_i.append({
                'name': '必修课平均绩点',
                'gradePoint': round(a_ / b_, 2),  # 计算当前学期必修课平均绩点
                'credit': b_  # 当前学期必修课总学分
            })
    
    # 如果有课程成绩，添加总平均绩点信息
    if g_b:
        data.append([{
            'name': '总平均绩点',
            'gradePoint': round(g_a / g_b, 2),  # 计算所有学期平均绩点
            'credit': g_b  # 所有学期总学分
        }])
    
    # 如果有必修课成绩，添加必修课总平均绩点信息
    if g_b_:
        data[-1].append({
            'name': '必修课总平均绩点',
            'gradePoint': round(g_a_ / g_b_, 2),  # 计算所有学期必修课平均绩点
            'credit': g_b_  # 所有学期必修课总学分
        })
    
    # 返回处理后的成绩数据
    return {
        'code': 0,
        'data': data
    }

