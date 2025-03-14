# coding=utf-8

from flask import request

from plugins_v3._login.login import login
from utils.decorators.check_sign import check_sign
from utils.decorators.request_limit import request_limit
from utils.exceptions import custom_abort
from . import api


@api.route('/login', methods=['GET'])
@check_sign(check_args={'name', 'passwd'})
@request_limit()
def handle_login():
    name = request.args.get('name', type=str)
    passwd = request.args.get('passwd', type=str)
    if len(name) == 8 or name[0].isalpha():
        custom_abort(-1, '小程序只支持本科生登录!')
    login(name, passwd, True)
    return {
        'code': 0,
        'message': 'OK'
    }

