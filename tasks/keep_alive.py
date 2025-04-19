from datetime import datetime, time
import logging

import requests
from global_config import PHONE, enableProxy
# from utils.send_message import sendmessage  # 注释掉短信发送模块导入
from utils.scheduler import scheduler
from utils.session import session
from utils.proxy_manager import proxy_manager  # 导入新的代理管理器

url = "https://zhjw.nuc.edu.cn/jwglxt/xtgl/index_initMenu.html?jsdm=xs&_t=1599980405581&ticket=ST-206697-Sd004wk15bKfNUsbirLI-zfsoft.com"
midnight = time(0, 0)
morning = time(7, 25)


def keep_alive():
    """
    保持与教务系统的连接，防止VPN关闭
    
    使用代理管理器在多个代理之间轮询，提高连接可靠性
    在凌晨0点到早上7点25分之间不发送警报，以避免干扰
    """
    if not enableProxy:
        # 如果禁用了代理功能，则跳过保活检查
        return
        
    try:
        # 使用代理管理器发起请求，自动处理代理轮询和故障转移
        response = proxy_manager.get(url, timeout=10, allow_redirects=False)
        
        # 检查响应状态码，302表示连接正常
        if response.status_code == 302:
            # logging.info('与教务系统连接中')
            return
            
    except requests.RequestException as e:
        # 所有代理都失败时会触发这个异常
        current_time = datetime.now().time()
        
        # 判断当前时间是否在凌晨0点到早上7点25分之间
        if midnight <= current_time <= morning:
            # 在指定时间范围内直接退出，不发送警报
            return
            
        logging.warning(f'无法连接至教务系统! 错误: {type(e).__name__} - {str(e)}')
        
        # 注释掉短信发送相关代码
        # for phone in PHONE:
        #     result = sendmessage([datetime.now().strftime("%H:%M:%S")], phone, '1908936')
        #     if result == 'Ok':
        #         logging.error("已向{}发送警报!".format(phone))
        #         break
        #     logging.error(result)
        #     logging.error("短信发送异常!")


scheduler.add_job(keep_alive, 'interval', seconds=15, next_run_time=datetime.now())
