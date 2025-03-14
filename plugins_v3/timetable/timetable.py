import re
import logging
from flask import request

from global_config import term_list, post_data as glo_data
from plugins_v3._login.login import login
from utils.decorators.cache import cache
from utils.decorators.check_sign import check_sign
from utils.decorators.request_limit import request_limit
from utils.session import session
from . import api, config
# 导入实验课程相关函数
from plugins_v3.experiment.experiment import (
    experiment_login, parse_experiment_from_teachn, merge_experiment_items
)
from plugins_v3.experiment import config as experiment_config
from utils.decorators.stopped import stopped


@api.route('/timetable', methods=['GET'])
@check_sign(check_args={'name', 'passwd'})
# @stopped()
@request_limit()
def handle_timetable():
    """
    获取当前学期课表接口
    
    请求参数:
    - name: 学号
    - passwd: 密码
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 课表数据，包含普通课程和实验课程
    """
    # 获取请求参数
    name = request.args.get('name', type=str)
    passwd = request.args.get('passwd', type=str)
    # 登录获取Cookie
    cookies = login(name, passwd)
    # 构建请求数据
    post_data = {
        'xnm': glo_data['xnm'],  # 学年
        'xqm': glo_data['xqm'],  # 学期
        'kzlx': 'ck'  # 查看类型
    }
    # 请求教务系统获取课表数据
    response = session.post(config.timetable_url, data=post_data, cookies=cookies)
    
    # 构建课表项目
    timetable_items = build_timetable_items(response.json())
    
    # 获取实验课程数据
    experiment_items = get_experiment_data(name, passwd)
    # 将实验课程合并到课表项目中
    timetable_items.extend(experiment_items)
    
    # 返回处理后的课表数据，包含普通课程和实验课程
    return {
        'code': 0,
        'data': timetable_items
    }


@api.route('/timetable/all', methods=['GET'])
@check_sign(check_args={'name', 'passwd'})
@stopped()
@request_limit()
def handle_timetable_all():
    """
    获取所有学期课表接口
    
    请求参数:
    - name: 学号
    - passwd: 密码
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 所有学期的课表数据，包含普通课程和实验课程
    """
    # 获取请求参数
    name = request.args.get('name', type=str)
    passwd = request.args.get('passwd', type=str)
    # 登录获取Cookie
    cookies = login(name, passwd)
    # 存储所有学期课表
    all_timetable = []
    # 遍历配置的所有学期
    for data in term_list:
        post_data = data['postData']
        term_name = data['name']
        # 请求教务系统获取该学期课表
        response = session.post(config.timetable_url, data=post_data, cookies=cookies)
        # 如果该学期没有课程，跳过
        if len(response.json()["kbList"]) == 0 and len(response.json()["sjkList"]) == 0:
            if len(all_timetable) == 0:
                continue
            else:
                info = {
                    'name': term_name,
                    'timetable': []
                }
                all_timetable.append(info)
                continue
        
        # 构建课表项目
        timetable_items = build_timetable_items(response.json())
        
        # 获取实验课程数据（仅对当前学期）
        if term_name == term_list[0]['name']:  # 如果是当前学期
            experiment_items = get_experiment_data(name, passwd)
            # 将实验课程合并到课表项目中
            timetable_items.extend(experiment_items)
        
        info = {
            'name': term_name,
            'timetable': timetable_items
        }
        all_timetable.append(info)
    return {
        'code': 0,
        'data': all_timetable
    }


def get_experiment_data(name, passwd):
    """
    获取实验课程数据
    
    参数:
    - name: 学号
    - passwd: 密码
    
    返回:
    - 实验课程列表
    """
    try:
        # 登录实验教学管理平台获取Cookie
        cookies = experiment_login(name, passwd)
        
        # 构建请求头
        headers = {
            'Referer': experiment_config.student_index_url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        
        # 访问实验教学管理平台首页
        teachn_url = f"http://{experiment_config.lab_host}/teachn/teachnAction/index.action"
        teachn_headers = headers.copy()
        teachn_headers["Referer"] = experiment_config.student_index_url
        
        teachn_response = session.get(teachn_url, headers=teachn_headers, cookies=cookies)
        teachn_content = None
        
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
            try:
                teachn_content = teachn_response.content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
                
        if teachn_content:
            # 解析实验课程数据
            experiment_items = parse_experiment_from_teachn(teachn_content)
            if experiment_items:
                # 合并相同课程和星期的实验课程
                experiment_items = merge_experiment_items(experiment_items)
                # 添加标记，表示这是实验课程
                for item in experiment_items:
                    item['isExperiment'] = True
                return experiment_items
        
        # 如果没有找到任何课程，返回空列表
        return []
        
    except Exception as e:
        logging.error(f"获取实验课程数据失败: {e}", exc_info=True)
        return []


def build_timetable_items(timetable):
    """
    构建课表项目列表
    
    参数:
    - timetable: 从教务系统获取的原始课表数据
    
    返回:
    - 处理后的课表项目列表，每个项目包含课程信息
    """
    timetable_items = []
    # 处理普通课程列表
    for table in timetable['kbList']:
        # 解析上课周次，例如 "4-11周" -> [4,5,6,7,8,9,10,11]
        weeks_str = table.get('zcd', '')  # 例如 "4-11周"
        weeks = []
        if weeks_str:
            # 检查是否包含单双周信息
            is_odd = '(单)' in weeks_str  # 单周
            is_even = '(双)' in weeks_str  # 双周
            
            # 移除单双周标记，便于后续处理
            weeks_str = weeks_str.replace('(单)', '').replace('(双)', '')
            
            # 分割多个周次范围，如"4-11周,13周"
            week_ranges = weeks_str.replace('周', '').split(',')
            for week_range in week_ranges:
                if '-' in week_range:
                    # 处理连续周，如"4-11"
                    start, end = map(int, week_range.split('-'))
                    # 根据单双周过滤
                    if is_odd:  # 单周
                        weeks.extend([w for w in range(start, end + 1) if w % 2 == 1])
                    elif is_even:  # 双周
                        weeks.extend([w for w in range(start, end + 1) if w % 2 == 0])
                    else:  # 所有周
                        weeks.extend(range(start, end + 1))
                else:
                    # 处理单周，如"13"
                    week = int(week_range)
                    # 根据单双周判断是否添加
                    if (not is_odd and not is_even) or \
                       (is_odd and week % 2 == 1) or \
                       (is_even and week % 2 == 0):
                        weeks.append(week)

        # 解析节次范围，例如 "3-4" -> start=3, end=4
        periods = table.get('jcor', '').split('-')
        start_period = int(periods[0]) if periods else 0
        end_period = int(periods[1]) if len(periods) > 1 else start_period

        # 构建课程项
        timetable_items.append({
            'title': table.get('kcmc', ''),  # 课程名称
            'location': f"{table.get('cdmc', '')}",  # 上课地点
            'weeks': weeks,  # 周次列表
            'dayOfWeek': int(table.get('xqj', 0)),  # 星期几
            'startPeriods': start_period,  # 开始节次
            'endPeriods': end_period,  # 结束节次
            'teacherName': table.get('xm', ''),  # 教师姓名
            'number': end_period - start_period + 1,  # 课程节数
            'isExperiment': False  # 标记为普通课程
        })

    # # 处理实践课
    # for practice in timetable.get('sjkList', []):
    #     # 实践课通常只需要课程名称
    #     timetable_items.append({
    #         'title': practice.get('sjkcgs', '')
    #     })

    return timetable_items
