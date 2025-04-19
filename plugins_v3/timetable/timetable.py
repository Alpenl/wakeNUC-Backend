import logging
from flask import request

from utils.decorators.cache import cache
from utils.decorators.check_sign import check_sign
from utils.decorators.request_limit import request_limit
from . import api
# 导入实验课程相关函数
from plugins_v3.experiment.experiment import get_experiment_data
# 导入普通课程相关函数
from plugins_v3.timetable.course import get_class_data


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
    
    try:
        # 获取普通课程数据 - 调用course.py中的函数
        class_items = get_class_data(name, passwd)
        
        # 获取实验课程数据 - 调用experiment.py中的函数
        experiment_items = get_experiment_data(name, passwd)
        
        # 合并普通课程和实验课程
        timetable_items = class_items + experiment_items
        
        # 返回处理后的课表数据
        return {
            'code': 0,
            'data': timetable_items
        }
    except Exception as e:
        logging.error(f"[课表] 获取课表数据失败: {str(e)}")
        return {
            'code': -1,
            'msg': f"获取课表数据失败: {str(e)}"
        }
