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
        
        # 存储所有页面的实验课程数据
        all_experiment_items = []
        current_page = 1
        total_pages = 1  # 初始化总页数为1
        
        # 获取当前学期信息（从第一页响应中获取）
        current_yearterm = ""  # 默认值
        
        while current_page <= total_pages:
            # 构建完整的URL，包含所有必要的查询参数
            query_params = {
                'page.pageNum': current_page,
                'currTeachCourseCode': '',
                'currWeek': '',
                'currYearterm': current_yearterm
            }
            # 构建查询字符串
            query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
            teachn_url = f"http://{experiment_config.lab_host}/teachn/teachnAction/index.action?{query_string}"
            
            teachn_headers = headers.copy()
            teachn_headers["Referer"] = experiment_config.student_index_url
            
            try:
                teachn_response = session.get(teachn_url, headers=teachn_headers, cookies=cookies)
                
                if teachn_response.status_code != 200:
                    logging.error(f"[实验课程] 请求失败，状态码: {teachn_response.status_code}")
                    continue
                
                teachn_content = None
                for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
                    try:
                        teachn_content = teachn_response.content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if not teachn_content:
                    logging.error("[实验课程] 无法解码响应内容")
                    continue
                
                # 解析实验课程数据
                experiment_items = parse_experiment_from_teachn(teachn_content)
                if experiment_items:
                    all_experiment_items.extend(experiment_items)
                
                # 获取总页数和学期信息（仅在第一页时获取）
                if current_page == 1:
                    from lxml import etree
                    tree = etree.HTML(teachn_content)
                    
                    # 查找包含页数信息的元素（在myPage div下的p标签中）
                    page_info = tree.xpath('//div[@id="myPage"]//p/text()')
                    if page_info:
                        page_text = page_info[0]  # 格式为 "第 1 页 / 共 2 页"
                        # 使用正则表达式提取总页数
                        total_pages_match = re.search(r'共\s*(\d+)\s*页', page_text)
                        if total_pages_match:
                            total_pages = int(total_pages_match.group(1))
                    
                    # 尝试从页面获取当前学期信息
                    yearterm_select = tree.xpath('//select[@name="currYearterm"]/option[@selected]/@value')
                    if yearterm_select:
                        current_yearterm = yearterm_select[0]
                
            except Exception as e:
                logging.error(f"[实验课程] 处理第 {current_page} 页时发生错误: {str(e)}")
            
            current_page += 1
        
        if all_experiment_items:
            # 合并相同课程的数据
            experiment_items = merge_experiment_items(all_experiment_items)
            # 添加标记，表示这是实验课程
            for item in experiment_items:
                item['isExperiment'] = True
            return experiment_items
        
        # 如果没有找到任何课程，返回空列表
        return []
        
    except Exception as e:
        logging.error(f"[实验课程] 获取实验课程数据失败: {str(e)}")
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
