import logging
from urllib.parse import urlencode
from flask import request

from global_config import app_id, app_secret
from utils.decorators.request_limit import request_limit
from utils.exceptions import custom_abort
from utils.session import session
from . import api


@api.route("/getopenid", methods=["GET"])
@request_limit(666)
def handle_exam():
    code = request.args.get('code', '')
    # 记录接收到的code
    logging.info(f"收到code请求: {code}")
    
    # 构建请求参数
    params = {
        'appid': app_id,
        'secret': app_secret,
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    
    try:
        # 记录发送的请求数据
        logging.info(f"发送请求到微信API，数据: {params}")
        
        # 使用 GET 方法请求微信接口
        url = f"https://api.weixin.qq.com/sns/jscode2session?{urlencode(params)}"
        response = session.get(url)
        
        # 记录原始响应
        logging.info(f"微信API响应: {response.text}")
        
        res = response.json()
        
        # 检查返回的数据中是否包含错误信息
        if 'errcode' in res and res['errcode'] != 0:
            logging.error(f"微信API返回错误: {res}")
            return {
                'code': -1,
                'message': f"微信API错误: {res.get('errmsg', '未知错误')}"
            }
            
        if 'openid' not in res:
            logging.error(f"响应中没有openid: {res}")
            return {
                'code': -1,
                'message': "获取openid失败"
            }
            
        logging.info("成功获取openid: " + res['openid'])
        return {
            'code': 0,
            'data': {
                'openId': res['openid']
            },
        }
    except Exception as e:
        logging.error(f"获取openid异常! 错误详情: {str(e)}")
        custom_abort(-1)



