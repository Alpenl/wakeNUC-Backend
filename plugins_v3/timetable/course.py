import re
import logging
from flask import request

from global_config import post_data as glo_data
from utils.session import session
from plugins_v3._login.login import login
from plugins_v3.timetable import config

def get_class_data(name, passwd):
    """
    获取普通课程数据
    
    参数:
    - name: 学号
    - passwd: 密码
    
    返回:
    - 普通课程列表
    """
    try:
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
        class_items = build_class_items(response.json())
        
        return class_items
        
    except Exception as e:
        logging.error(f"[普通课程] 获取课程数据失败: {str(e)}")
        return []

def build_class_items(timetable):
    """
    构建普通课表项目列表
    
    参数:
    - timetable: 从教务系统获取的原始课表数据
    
    返回:
    - 处理后的普通课表项目列表，每个项目包含课程信息
    """
    class_items = []
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
        class_items.append({
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
    #     class_items.append({
    #         'title': practice.get('sjkcgs', '')
    #     })

    return class_items 