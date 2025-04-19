import re
from flask import request

from utils.decorators.check_sign import check_sign
from utils.session import session
from plugins_v3.experiment import config
from lxml import etree
from plugins_v3._login.login import experiment_login
from utils.decorators.request_limit import request_limit
from utils.decorators.cache import cache
from utils.redis_connections import redis_experiment
import logging
from . import api


@api.route('/experiment', methods=['GET'])
@check_sign(check_args={'name', 'passwd'})  # 验证请求签名
@request_limit(5)                           # 限制请求频率，每分钟最多5次
@cache({'name'}, 300)                       # 缓存结果300秒
def experiment():
    """
    获取学生实验课程信息
    
    查询参数:
    - name: 学号
    - passwd: 密码
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 实验课程列表，包含课程名称、时间、地点和教师姓名
    """
    # 获取请求参数
    name = request.args.get('name', type=str)
    passwd = request.args.get('passwd', type=str)
    
    try:
        # 登录实验教学管理平台获取Cookie
        cookies = experiment_login(name, passwd)
        logging.info(f"成功获取实验系统Cookie: {cookies}")
        
        # 构建请求头
        headers = {
            'Referer': config.student_index_url,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        
        # 访问实验教学管理平台首页
        logging.info("访问实验教学管理平台首页")
        teachn_url = f"http://{config.lab_host}/teachn/teachnAction/index.action"
        teachn_headers = headers.copy()
        teachn_headers["Referer"] = config.student_index_url
        
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
                logging.info(f"成功解析到 {len(experiment_items)} 条实验课程信息")
                return {
                    'code': 0,
                    'data': experiment_items
                }
        
        # 如果没有找到任何课程，返回空列表
        logging.warning("未找到任何实验课程信息")
        return {
            'code': 0,
            'data': []
        }
        
    except Exception as e:
        logging.error(f"获取实验课程信息失败: {e}", exc_info=True)
        return {
            'code': -1,
            'msg': f"获取实验课程信息失败: {str(e)}"
        }

def get_experiment_data(name, passwd):
    """
    获取实验课程数据，为课表提供适配的实验课程数据格式
    
    参数:
    - name: 学号
    - passwd: 密码
    
    返回:
    - 处理后的实验课程列表，添加了isExperiment标记
    """
    try:
        # 登录实验教学管理平台获取Cookie
        cookies = experiment_login(name, passwd)
        
        # 构建请求头
        headers = {
            'Referer': config.student_index_url,
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
            teachn_url = f"http://{config.lab_host}/teachn/teachnAction/index.action?{query_string}"
            
            teachn_headers = headers.copy()
            teachn_headers["Referer"] = config.student_index_url
            
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

def parse_experiment_from_teachn(html_content):
    """
    从teachnAction/index.action页面解析实验课程信息
    
    参数:
    - html_content: 实验系统返回的HTML内容
    
    返回:
    - 处理后的实验课程列表，只包含指定字段
    """
    experiment_items = []
    
    # 将HTML字符串转换为Element对象，用于XPath解析
    tree = etree.HTML(html_content)
    
    # 获取表格中的所有行
    rows = tree.xpath('//table[@class="tablelist"]/tbody/tr')
    if not rows:
        rows = tree.xpath('//table[@class="tablelist"]//tr')
    if not rows:
        rows = tree.xpath('//table//tr[position()>1]')  # 跳过表头行
    
    # logging.info(f"备用方法找到 {len(rows)} 行实验课程数据")
    
    # 遍历每一行，提取实验课程信息
    for row in rows:
        # 跳过表头行
        if row.xpath('.//th'):
            continue
            
        # 选择当前行下的所有<td>元素
        cells = row.xpath('.//td')
        
        # 如果没有足够的单元格，跳过这一行
        if len(cells) < 5:
            continue
        
        try:
            # 课程名称 - 通常在第一列，可能包含在strong标签中
            course_name_elem = cells[0].xpath('.//strong')
            if course_name_elem:
                course_name = course_name_elem[0].xpath('normalize-space(.)')
            else:
                course_name = cells[0].xpath('normalize-space(.)')
                
            if not course_name or course_name == "课程名称":
                continue
                
            # 解析上课时间，例如 "4周星期六05-08节"
            time_text = cells[2].xpath('normalize-space(.)')
            
            # 提取周次，支持多种格式
            weeks = []
            # 尝试匹配连续周次，如"2-9周"
            week_range_match = re.search(r'(\d+)-(\d+)周', time_text)
            if week_range_match:
                start_week = int(week_range_match.group(1))
                end_week = int(week_range_match.group(2))
                weeks.extend(range(start_week, end_week + 1))
            else:
                # 尝试匹配单周，如"4周"
                week_match = re.search(r'(\d+)周', time_text)
                if not week_match:
                    week_match = re.search(r'第(\d+)周', time_text)
                if week_match:
                    week = int(week_match.group(1))
                    weeks = [week] if week > 0 else []
            
            # 提取星期几
            day_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '日': 7, '天': 7}
            day_match = re.search(r'星期([一二三四五六日天])', time_text)
            day_of_week = day_map.get(day_match.group(1), 0) if day_match else 0
            
            # 提取节次
            period_match = re.search(r'(\d+)-(\d+)节', time_text)
            if period_match:
                start_period = int(period_match.group(1))
                end_period = int(period_match.group(2))
            else:
                # 尝试匹配单节课，如"第3节"
                single_period_match = re.search(r'(\d+)节', time_text)
                start_period = int(single_period_match.group(1)) if single_period_match else 0
                end_period = start_period
            
            # 上课地点
            location = cells[3].xpath('normalize-space(.)')
            
            # 教师姓名
            teacher_name = cells[4].xpath('normalize-space(.)')
            
            # 构建课程项，只包含指定字段
            experiment_item = {
                'title': course_name,  # 课程名称
                'location': location,  # 上课地点
                'weeks': weeks,  # 周次列表
                'dayOfWeek': day_of_week,  # 星期几
                'startPeriods': start_period,  # 开始节次
                'endPeriods': end_period,  # 结束节次
                'teacherName': teacher_name,  # 教师姓名
                'number': end_period - start_period + 1  # 课程节数
            }
            
            experiment_items.append(experiment_item)
            
        except Exception as e:
            logging.error(f"解析行数据时出错: {e}", exc_info=True)
            continue
    
    return experiment_items

def merge_experiment_items(experiment_items):
    """
    合并相同课程名称和星期的实验课程，并将连续的节次也进行合并
    
    参数:
    - experiment_items: 解析得到的实验课程列表
    
    返回:
    - 合并后的实验课程列表
    """
    if not experiment_items:
        return []
        
    # 按课程名称和星期几分组
    grouped_items = {}
    for item in experiment_items:
        # 创建分组键：课程名称+星期几
        key = (item['title'], item['dayOfWeek'])
        if key not in grouped_items:
            grouped_items[key] = []
        grouped_items[key].append(item)
    
    # 合并后的结果
    merged_items = []
    
    # 处理每个分组
    for (title, day_of_week), items in grouped_items.items():
        # 如果只有一个项目，直接添加
        if len(items) == 1:
            merged_items.append(items[0])
            continue
            
        # 按地点和教师分组
        location_teacher_groups = {}
        for item in items:
            lt_key = (item['location'], item['teacherName'])
            if lt_key not in location_teacher_groups:
                location_teacher_groups[lt_key] = []
            location_teacher_groups[lt_key].append(item)
            
        # 处理每个地点和教师分组
        for (location, teacher), lt_items in location_teacher_groups.items():
            # 合并周次
            all_weeks = []
            for item in lt_items:
                all_weeks.extend(item['weeks'])
            all_weeks = sorted(list(set(all_weeks)))  # 去重并排序
            
            # 检查是否有连续的节次可以合并
            # 按开始节次排序
            lt_items.sort(key=lambda x: (x['startPeriods'], x['endPeriods']))
            
            # 合并连续的节次
            merged_periods = []
            current_start = lt_items[0]['startPeriods']
            current_end = lt_items[0]['endPeriods']
            
            for i in range(1, len(lt_items)):
                if lt_items[i]['startPeriods'] <= current_end + 1:
                    # 可以合并
                    current_end = max(current_end, lt_items[i]['endPeriods'])
                else:
                    # 不能合并，保存当前区间
                    merged_periods.append((current_start, current_end))
                    current_start = lt_items[i]['startPeriods']
                    current_end = lt_items[i]['endPeriods']
            
            # 添加最后一个区间
            merged_periods.append((current_start, current_end))
            
            # 创建合并后的项目
            for start_period, end_period in merged_periods:
                merged_item = {
                    'title': title,
                    'location': location,
                    'weeks': all_weeks,
                    'dayOfWeek': day_of_week,
                    'startPeriods': start_period,
                    'endPeriods': end_period,
                    'teacherName': teacher,
                    'number': end_period - start_period + 1
                }
                merged_items.append(merged_item)
    
    return merged_items
