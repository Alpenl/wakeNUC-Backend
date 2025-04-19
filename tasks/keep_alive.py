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

# 上一次连接状态，True表示连接正常，False表示连接失败
last_connection_status = True

def keep_alive():
    """
    保持与教务系统的连接
    
    当无法连接教务系统时立即切换到下一个代理
    在凌晨0点到早上7点25分之间不发送警报，以避免干扰
    """
    global last_connection_status
    
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
            # 连接成功
            # 只有在之前连接失败的情况下才记录恢复连接的日志
            if not last_connection_status:
                logging.info('恢复与教务系统的连接')
                last_connection_status = True
            
            # 设置代理状态为正常
            global_values.set_value("proxy_status_ok", True)
            return
            
    except requests.RequestException as e:
        # 请求异常，立即切换到下一个代理
        error_type = type(e).__name__
        
        # 设置代理状态为不正常
        global_values.set_value("proxy_status_ok", False)
        
        # 记录连接失败状态
        last_connection_status = False
        
        # 切换到下一个代理 - 先存储当前代理索引
        current_index = proxy_manager.current_proxy_index
        proxy_manager.switch_to_next_proxy()
        
        # 获取下一个代理信息
        next_index = (current_index + 1) % len(proxy_list)
        proxy_url = proxy_list[next_index].get('url', '')
        proxy_type = proxy_list[next_index].get('type', 'http')
        
        # 记录简化的错误信息
        logging.warning(f'无法连接至教务系统! 错误: {error_type}, 已切换代理至 #{next_index+1}: {proxy_type}://{proxy_url}')
        logging.debug(f'错误详情: {str(e)}')


scheduler.add_job(keep_alive, 'interval', seconds=15, next_run_time=datetime.now())
