from flask import jsonify
from . import api
import datetime

# 第一周日期时间
@api.route('/static/firstWeekDateTime', methods=['GET'])
def first_week_date_time():
    """获取学期第一周的日期时间"""
    # 这里设置为2024年春季学期第一周的时间
    return jsonify({
        'code': 0,
        'data': '2024-02-26'  # 根据实际学期开始时间调整
    })

# 假期信息
@api.route('/v3/vacation', methods=['GET'])
def vacation():
    """获取假期信息"""
    return jsonify({
        'code': 0,
        'data': {
            'start': '2024-01-14',  # 寒假开始时间
            'end': '2024-02-25'     # 寒假结束时间
        }
    })

# 轮播图
@api.route('/v3/slides', methods=['GET'])
def slides():
    """获取首页轮播图"""
    return jsonify({
        'code': 0,
        'data': [
            {
                'id': 1,
                'image': 'https://example.com/slide1.jpg',
                'url': 'https://example.com/news/1',
                'title': '校园新闻1'
            }
            # 可以添加更多轮播图
        ]
    })

# 新闻
@api.route('/v3/news/<int:category>', methods=['GET'])
def news(category):
    """获取指定分类的新闻列表"""
    return jsonify({
        'code': 0,
        'data': {
            'list': [
                {
                    'id': 1,
                    'title': '示例新闻标题',
                    'date': '2024-03-05',
                    'url': 'https://example.com/news/1'
                }
            ],
            'total': 1
        }
    })

# 天气
@api.route('/v3/weather', methods=['GET'])
def weather():
    """获取天气信息"""
    return jsonify({
        'code': 0,
        'data': {
            'temperature': '15°C',
            'weather': '晴',
            'wind': '东北风3级',
            'humidity': '65%'
        }
    })