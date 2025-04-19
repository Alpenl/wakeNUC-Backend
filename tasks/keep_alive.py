from datetime import datetime, time
import logging
import requests
from global_config import PHONE, enableProxy, proxy_list
# from utils.send_message import sendmessage  # 注释掉短信发送模块导入
from utils.scheduler import scheduler
from utils.session import session
from utils.proxy_manager import proxy_manager  # 导入新的代理管理器
from utils.gol import global_values

url = "https://zhjw.nuc.edu.cn/jwglxt/xtgl/index_initMenu.html?jsdm=xs&_t=1599980405581&ticket=ST-206697-Sd004wk15bKfNUsbirLI-zfsoft.com"
midnight = time(0, 0)
morning = time(7, 25)
# 记录连续失败次数
consecutive_failures = 0
# 最大连续失败次数，超过此值才发出警告
max_failures_before_warning = 3

def keep_alive():
    """
    保持与教务系统的连接
    
    当无法连接教务系统时立即切换到下一个代理
    在凌晨0点到早上7点25分之间不发送警报，以避免干扰
    """
    global consecutive_failures
    
    if not enableProxy:
        # 如果禁用了代理功能，则跳过保活检查
        return
    
    # 如果没有配置代理，则跳过检查
    if not proxy_list or len(proxy_list) == 0:
        return
        
    try:
        # 使用当前系统代理发起请求
        response = proxy_manager.get(url, timeout=10, allow_redirects=False)
        
        # 检查响应状态码，302表示连接正常
        if response.status_code == 302:
            # 连接成功，重置连续失败计数
            if consecutive_failures > 0:
                logging.info(f'恢复与教务系统的连接，之前连续失败 {consecutive_failures} 次')
                consecutive_failures = 0
            
            # 设置代理状态为正常
            global_values.set_value("proxy_status_ok", True)
            return
            
    except requests.RequestException as e:
        # 请求异常，立即切换到下一个代理
        logging.warning(f'无法连接至教务系统! 错误: {type(e).__name__}')
        logging.debug(f'错误详情: {str(e)}')
        
        # 切换到下一个代理
        proxy_manager.switch_to_next_proxy()
        
        # 增加连续失败计数
        consecutive_failures += 1
        
        # 设置代理状态为不正常
        global_values.set_value("proxy_status_ok", False)
        
        # 判断是否需要发出警告（避免刷屏）
        current_time = datetime.now().time()
        if (current_time < midnight or current_time > morning) and consecutive_failures >= max_failures_before_warning:
            logging.warning(f'无法连接至教务系统! 连续失败 {consecutive_failures} 次，已切换代理')
            
            # 注释掉短信发送相关代码
            # for phone in PHONE:
            #     result = sendmessage([datetime.now().strftime("%H:%M:%S")], phone, '1908936')
            #     if result == 'Ok':
            #         logging.error("已向{}发送警报!".format(phone))
            #         break
            #     logging.error(result)
            #     logging.error("短信发送异常!")


scheduler.add_job(keep_alive, 'interval', seconds=15, next_run_time=datetime.now())
