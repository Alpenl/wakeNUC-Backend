from global_config import NAME, PASSWD, post_data as glo_data
from utils.decorators.cache import cache
from utils.decorators.check_sign import check_sign
from utils.decorators.request_limit import request_limit
from utils.exceptions import custom_abort
from utils.session import session
from . import api, config
from .._login.login import login


@api.route("/emptyClassroom/<string:building_id>/<int:week_of_term>/<int:day_of_week>/<int:class_of_day>",
           methods=['GET'])
@check_sign(set())      # 验证请求签名
@request_limit()        # 限制请求频率
@cache(set())           # 缓存结果
def handle_empty_classroom(building_id: str, week_of_term: int, day_of_week: int, class_of_day: int):
    """
    查询指定条件下的空闲教室（单节课）
    
    路径参数:
    - building_id: 教学楼编号
    - week_of_term: 学期第几周
    - day_of_week: 星期几（1-7）
    - class_of_day: 第几节课（1-12）
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 空闲教室列表，包含位置、教室号、座位数和座位类型
    """
    # 使用管理员账号登录获取Cookie
    cookies = login(NAME, PASSWD)

    # 构建请求数据
    post_data = {
        "fwzt": "cx",                      # 查询功能
        'xnm': glo_data['xnm'],            # 学年
        'xqm': glo_data['xqm'],            # 学期
        "lh": building_id,                 # 楼号
        "jyfs": "0",                       # 教育方式
        "zcd": 2 ** (week_of_term - 1),    # 周次，使用二进制位表示
        "xqj": day_of_week,                # 星期几
        "jcd": 2 ** (class_of_day - 1),    # 节次，使用二进制位表示
        "queryModel.showCount": "1001"     # 最大返回数量
    }
    
    # 请求教务系统获取空教室信息
    items = session.post(config.empty_classroom_url, post_data, cookies=cookies)
    if items.content.decode() == 'null':
        custom_abort(-1, '暂无空闲教室!')
    items = items.json()
    items = items["items"]
    
    # 处理返回的空教室数据
    data = []
    for item in items:
        room = {
            "location": item["cdlbmc"],                # 教室位置/类别名称
            "roomId": item["cdmc"],                    # 教室编号/名称
            "seats": item.get("zws", 0),               # 座位数量
            "seatType": item.get("bz", "正常座椅")      # 座位类型
        }
        data.append(room)

    # 返回处理后的空教室数据
    return {
        'code': 0,
        'data': data
    }


@api.route("/emptyClassroom/<string:building_id>/<int:week_of_term>/<int:day_of_week>/<int:start_class>/<int:end_class>",
    methods=['GET'])
@check_sign(set())      # 验证请求签名
@request_limit()        # 限制请求频率
@cache(set())           # 缓存结果
def handle_filter_empty_classroom(building_id: str, week_of_term: int, day_of_week: int, start_class: int, end_class):
    """
    查询指定条件下的空闲教室（连续多节课）
    
    路径参数:
    - building_id: 教学楼编号
    - week_of_term: 学期第几周
    - day_of_week: 星期几（1-7）
    - start_class: 开始节次
    - end_class: 结束节次
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 空闲教室列表，包含位置、教室号、座位数和座位类型
    """
    # 使用管理员账号登录获取Cookie
    cookies = login(NAME, PASSWD)
    
    # 计算连续多节课的二进制表示
    section = 0
    for i in range(start_class - 1, end_class):
        section |= (1 << i)  # 使用位运算设置对应节次的位
    
    # 构建请求数据
    post_data = {
        "fwzt": "cx",                      # 查询功能
        'xnm': glo_data['xnm'],            # 学年
        'xqm': glo_data['xqm'],            # 学期
        "lh": building_id,                 # 楼号
        "jyfs": "0",                       # 教育方式
        "zcd": 1 << (week_of_term - 1),    # 周次，使用二进制位表示
        "xqj": day_of_week,                # 星期几
        "jcd": section,                    # 节次，使用二进制位表示连续多节
        "queryModel.showCount": "1001"     # 最大返回数量
    }

    # 请求教务系统获取空教室信息
    classrooms = session.post(config.empty_classroom_url, post_data, cookies=cookies).json()

    # 处理返回的空教室数据
    classrooms = classrooms["items"]
    res = []
    for item in classrooms:
        res.append({
            "location": item["cdlbmc"],                # 教室位置/类别名称
            "roomId": item["cdmc"],                    # 教室编号/名称
            "seats": item.get("zws", 0),               # 座位数量
            "seatType": item.get("bz", "正常座椅")      # 座位类型
        })
    
    # 返回处理后的空教室数据
    return {
        'code': 0,
        'data': res
    }
