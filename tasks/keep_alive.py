from datetime import datetime, time
import logging

import requests
from global_config import PHONE
# from utils.send_message import sendmessage  # 注释掉短信发送模块导入
from utils.scheduler import scheduler
from utils.session import session

url = "https://zhjw.nuc.edu.cn/jwglxt/xtgl/index_initMenu.html?jsdm=xs&_t=1599980405581&ticket=ST-206697-Sd004wk15bKfNUsbirLI-zfsoft.com"
midnight = time(0, 0)
morning = time(7, 25)


def keep_alive():
    try:
        # 保持心跳 防止vpn关闭
        if session.get(url, timeout=10, allow_redirects=False).status_code == 302:
            # logging.info('与教务系统连接中')
            return
    except requests.RequestException:
        current_time = datetime.now().time()
        if midnight <= current_time <= morning:
            # 判断当前时间是否在凌晨0点到早上7点25分之间
            # 是的话直接退出
            return
        logging.warning('无法连接至教务系统!')
        # 注释掉短信发送相关代码
        # for phone in PHONE:
        #     result = sendmessage([datetime.now().strftime("%H:%M:%S")], phone, '1908936')
        #     if result == 'Ok':
        #         logging.error("已向{}发送警报!".format(phone))
        #         break
        #     logging.error(result)
        #     logging.error("短信发送异常!")


scheduler.add_job(keep_alive, 'interval', seconds=15, next_run_time=datetime.now())
