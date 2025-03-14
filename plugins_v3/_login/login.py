import logging
import pickle
import re

import requests
from requests import Response
from requests.cookies import RequestsCookieJar
from utils.myrsa import Encrypt
from plugins_v3._login import config
from utils.exceptions import custom_abort
from utils.redis_connections import redis_session, redis_experiment
from utils.session import session


# 主体账号登录函数
def login(name: str, passwd: str, disable_cache=False, all_cookies=True) -> RequestsCookieJar:
    """
    统一身份认证系统登录函数
    
    工作流程：
    1. 检查参数有效性
    2. 尝试从缓存获取有效的Cookie
    3. 如果缓存无效，则执行完整的登录流程
    4. 缓存新的Cookie用于后续请求
    
    :param name: 学号
    :param passwd: 密码
    :param disable_cache: 是否禁用缓存，默认False
    :param all_cookies: 是否获取所有系统的Cookie，默认True
    :return: 包含登录凭证的Cookie对象
    """
    if not name or not passwd:
        custom_abort(-3, '账号密码不能为空!')
    if name.strip() != name:
        custom_abort(-3, '用户名包含空字符!')
    # 如果存在缓存且未禁用缓存
    if not disable_cache:
        # 尝试从Redis获取缓存的Cookie
        cookie_pickle = redis_session.get("cookie" + name)
        if cookie_pickle:
            # 反序列化Cookie对象
            cookies: RequestsCookieJar = pickle.loads(cookie_pickle)
            # 测试Cookie是否有效
            r = session.get(config.login_test_url, allow_redirects=False, cookies=cookies)
            # 尝试使用不同的编码方式解码内容
            content = None
            for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
                try:
                    content = r.content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            # 如果保存的cookie可以正常使用的话
            if r.status_code == 200 and content and content.find("自定义门户") != -1:
                # 更新Cookie
                cookies.update(r.cookies)
                if all_cookies:
                    # 清除可能存在的无效域名Cookie
                    if ".222.31.49.139" in cookies.keys():
                        cookies.clear(".222.31.49.139")
                    # 获取教务系统Cookie
                    res, cookies = follow_link(cookies, config.jwxt_url)
                    # 尝试使用不同的编码方式解码内容
                    content = None
                    for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
                        try:
                            content = res.content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    # 如果保存的cookie可以正常进入教务系统
                    if res.status_code == 200 and content and content.find("教学管理信息服务平台") != -1:
                        # 更新缓存并设置过期时间（6小时）
                        redis_session.set("cookie" + name, pickle.dumps(cookies), ex=21600)
                        # 命中缓存，返回有效Cookie
                        return cookies
                    else:
                        # Cookie无效，删除缓存
                        redis_session.delete("cookie" + name)
                        logging.info("cookies" + name + "过期删除, code为:" + str(res.status_code))
    # 未命中缓存或缓存无效，执行完整登录流程
    login_response, cookies = re_login(re_url=config.index_url, e_url=config.e_login_url, name=name, passwd=passwd)
    # 检查登录结果
    cookies = check_login(cookies=cookies, login_response=login_response)
    if all_cookies:
        # 获取教务系统cookie
        _, cookies = follow_link(cookies, config.jwxt_url)
    # 缓存Cookie，设置过期时间（6小时）
    redis_session.set("cookie" + name, pickle.dumps(cookies), ex=21600)
    return cookies


# 实验系统登录
def experiment_login(name: str, passwd: str) -> RequestsCookieJar:
    """
    实验系统登录函数
    
    工作流程：
    1. 尝试从缓存获取有效的Cookie
    2. 如果缓存无效，则使用统一认证系统的Cookie获取实验系统的Cookie
    
    :param name: 学号
    :param passwd: 密码
    :return: 包含登录凭证的Cookie对象
    """
    from plugins_v3.experiment import config as exp_config
    
    # 尝试从缓存获取Cookie
    cookie_pickle = redis_experiment.get("experiment" + name)
    # 如果命中缓存
    if cookie_pickle:
        cookies: RequestsCookieJar = pickle.loads(cookie_pickle)
        try:
            r = session.get(exp_config.index_url + "1", allow_redirects=False, cookies=cookies)
            # 尝试使用不同的编码方式解码内容
            content = None
            for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
                try:
                    content = r.content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
                    
            # 如果缓存可以正常使用
            if r.status_code == 200 and content and ("中北大学实践教学管理平台" in content or "实验教学管理平台" in content):
                cookies.update(r.cookies)
                redis_experiment.set("experiment" + name, pickle.dumps(cookies), ex=21600)
                return cookies
            else:
                redis_experiment.delete("experiment" + name)
        except Exception as e:
            redis_experiment.delete("experiment" + name)
            logging.error(f"验证缓存Cookie时出错: {e}")

    # 未命中缓存，使用统一认证系统的Cookie获取实验系统的Cookie
    try:
        # 1. 获取统一认证系统的Cookie
        auth_cookies = login(name, passwd)
        
        # 2. 调用获取实验室系统Cookie的函数
        merged_cookies = get_lab_cookie(auth_cookies)
        
        if not merged_cookies:
            custom_abort(-1, "实验系统登录失败：无法获取有效的Cookie")
        
        # 3. 缓存Cookie
        redis_experiment.set("experiment" + name, pickle.dumps(merged_cookies), ex=21600)
        
        return merged_cookies
    except Exception as e:
        logging.error(f"实验系统登录过程中出错: {e}", exc_info=True)
        raise e


def get_lab_cookie(auth_cookies: RequestsCookieJar) -> RequestsCookieJar:
    """
    使用统一认证系统的Cookie获取实验室系统的Cookie
    
    工作流程：
    1. 访问实验系统入口URL，获取重定向到CAS的URL
    2. 携带统一认证Cookie访问CAS URL，获取带ticket的重定向URL
    3. 访问带ticket的URL，获取JSESSIONID并获取下一个重定向URL
    4. 访问带jsessionid的URL，获取aexpsid并获取重定向到学生首页的URL
    5. 访问学生首页，完成登录流程
    6. 访问实验教学管理平台首页，验证Cookie有效性
    
    :param auth_cookies: 统一认证系统的Cookie
    :return: 合并后的Cookie对象，如果获取失败则返回None
    """
    from plugins_v3.experiment import config as exp_config
    
    try:
        # 设置通用请求头
        common_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # 步骤1: 访问实验系统入口URL，获取重定向到CAS的URL
        step1_url = exp_config.lab_service_url
        step1_headers = common_headers.copy()
        step1_headers["Host"] = exp_config.lab_host
        
        step1_response = session.get(step1_url, headers=step1_headers, allow_redirects=False)
        
        if step1_response.status_code != 302 or "Location" not in step1_response.headers:
            return None
            
        # 获取重定向到CAS的URL
        cas_url = step1_response.headers["Location"]
        
        # 步骤2: 携带统一认证Cookie访问CAS URL，获取带ticket的重定向URL
        step2_headers = common_headers.copy()
        step2_headers["Host"] = "zhrz.nuc.edu.cn"
        
        step2_response = session.get(cas_url, headers=step2_headers, cookies=auth_cookies, allow_redirects=False)
        
        if step2_response.status_code != 302 or "Location" not in step2_response.headers:
            return None
            
        # 获取带ticket的重定向URL
        ticket_url = step2_response.headers["Location"]
        
        # 步骤3: 访问带ticket的URL，获取JSESSIONID并获取下一个重定向URL
        step3_headers = common_headers.copy()
        step3_headers["Host"] = exp_config.lab_host
        
        step3_response = session.get(ticket_url, headers=step3_headers, allow_redirects=False)
        
        if step3_response.status_code != 302 or "Location" not in step3_response.headers:
            return None
            
        # 获取JSESSIONID
        lab_cookies = step3_response.cookies
        jsessionid = None
        for cookie in lab_cookies:
            if cookie.name == "JSESSIONID":
                jsessionid = cookie.value
                break
                
        if not jsessionid:
            return None
            
        # 获取下一个重定向URL（带jsessionid的URL）
        jsessionid_url = step3_response.headers["Location"]
        
        # 步骤4: 访问带jsessionid的URL，获取aexpsid并获取重定向到学生首页的URL
        step4_headers = common_headers.copy()
        step4_headers["Host"] = exp_config.lab_host
        
        step4_response = session.get(jsessionid_url, headers=step4_headers, cookies=lab_cookies, allow_redirects=False)
        
        if step4_response.status_code != 302 or "Location" not in step4_response.headers:
            return None
            
        # 更新Cookie，获取aexpsid
        lab_cookies.update(step4_response.cookies)
        aexpsid = None
        for cookie in lab_cookies:
            if cookie.name == "aexpsid":
                aexpsid = cookie.value
                break
        
        # 获取学生首页URL
        student_index_url = step4_response.headers["Location"]
        
        # 步骤5: 访问学生首页，完成登录流程
        step5_headers = common_headers.copy()
        step5_headers["Host"] = exp_config.lab_host
        
        step5_response = session.get(student_index_url, headers=step5_headers, cookies=lab_cookies, allow_redirects=False)
        
        # 更新Cookie
        lab_cookies.update(step5_response.cookies)
        
        # 再次检查是否获取到aexpsid（如果之前没有获取到）
        if not aexpsid:
            for cookie in lab_cookies:
                if cookie.name == "aexpsid":
                    aexpsid = cookie.value
                    break
        
        # 步骤6: 访问实验教学管理平台首页，验证Cookie有效性
        # 先访问左侧菜单页面，获取正确的Referer
        left_menu_url = f"http://{exp_config.lab_host}/aexp/stuLeft.jsp"
        
        left_menu_headers = common_headers.copy()
        left_menu_headers["Host"] = exp_config.lab_host
        
        left_menu_response = session.get(left_menu_url, headers=left_menu_headers, cookies=lab_cookies)
        
        # 访问实验教学管理平台首页
        teachn_url = f"http://{exp_config.lab_host}/teachn/teachnAction/index.action"
        
        teachn_headers = common_headers.copy()
        teachn_headers["Host"] = exp_config.lab_host
        teachn_headers["Referer"] = left_menu_url  # 设置正确的Referer
        
        teachn_response = session.get(teachn_url, headers=teachn_headers, cookies=lab_cookies)
        
        # 更新Cookie
        lab_cookies.update(teachn_response.cookies)
        
        # 构建最终的Cookie对象
        final_cookies = RequestsCookieJar()
        
        # 只保留必要的Cookie
        for cookie in lab_cookies:
            if cookie.name in ["JSESSIONID", "aexpsid"]:
                final_cookies.set(cookie.name, cookie.value, domain=cookie.domain or exp_config.lab_host, path=cookie.path or "/")
        
        # 检查是否同时获取到了JSESSIONID和aexpsid
        has_jsessionid = "JSESSIONID" in [cookie.name for cookie in final_cookies]
        has_aexpsid = "aexpsid" in [cookie.name for cookie in final_cookies]
        
        # 尝试补全缺失的Cookie
        if not has_jsessionid and jsessionid:
            final_cookies.set("JSESSIONID", jsessionid, domain=exp_config.lab_host, path="/")
        if not has_aexpsid and aexpsid:
            final_cookies.set("aexpsid", aexpsid, domain=exp_config.lab_host, path="/")
        
        return final_cookies
        
    except Exception as e:
        logging.error(f"获取实验室系统Cookie时出错: {e}", exc_info=True)
        return None


# 体育管理系统登录
def physical_login(name: str, passwd: str) -> RequestsCookieJar:
    login_response, cookies = re_login(re_url=config.physical_url, e_url=config.e_physical_url, name=name, passwd=passwd)
    # 正式迭代登录并判断登录结果
    cookies = check_login(cookies=cookies, login_response=login_response)
    return cookies


# 登录以及重新登录
def re_login(re_url, e_url, name, passwd):
    re_num = 0
    while True:
        try:
            index_response = session.get(re_url)
            if not index_response.ok:
                logging.error(f"Failed to get login page, status code: {index_response.status_code}")
                custom_abort(-1, '登录系统暂时无法访问，请稍后再试!')
            
            # 尝试使用不同的编码方式解码内容
            content = None
            for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
                try:
                    content = index_response.content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
                    
            if not content:
                logging.error("无法解码登录页面响应内容")
                custom_abort(-1, '登录系统暂时无法访问，请稍后再试!')
                
            if content.find("Loading...") != -1:
                custom_abort(-1, 'VPN通道已关闭!')
                
            # 获取用于提交登录的数据和cookie
            cookies, post_data = ready_login(index_response=index_response, name=name, passwd=passwd)
            
            # 提交登录
            login_response = session.post(re_url, allow_redirects=False, data=post_data, cookies=cookies)
            
            if login_response.headers.get('Location') != e_url or re_num > 3:
                break
                
            re_num += 1
            logging.warning('{}登录异常,第{}次重新发送登录请求!'.format(name, re_num))
            
        except Exception as e:
            logging.error(f"Login attempt failed: {str(e)}")
            if re_num > 3:
                custom_abort(-1, '登录失败，请稍后重试!')
            re_num += 1
            continue
            
    return login_response, cookies


# 跟随一系列 302 跳转，并更新 cookies
def follow_link(cookies: RequestsCookieJar, url: str) -> (Response, RequestsCookieJar):
    while True:
        resp = session.get(url, cookies=cookies, allow_redirects=False)
        cookies.update(resp.cookies)
        # session中已经拒绝了https,所以这里是http
        if not resp.headers.get('location') or resp.headers.get('location').find('http') == -1:
            return resp, cookies
        else:
            url = resp.headers.get('location')


# 请求的数据
def ready_login(index_response: Response, name: str, passwd: str):
    cookies = index_response.cookies
    
    # 尝试使用不同的编码方式解码内容
    content = None
    for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
        try:
            content = index_response.content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
            
    if not content:
        logging.error("无法解码登录页面响应内容")
        custom_abort(-1, '登录系统暂时无法访问，请稍后再试!')
    
    # Check if we got a valid response with the execution value
    execution_match = re.search('name="execution" value="(.*?)"', content)
    if not execution_match:
        # Log the response content for debugging
        logging.error(f"Failed to find execution value in response. Content: {content[:200]}...")
        custom_abort(-1, '登录系统暂时无法访问，请稍后再试!')
        
    execution = execution_match.group(1)
    
    try:
        public_key_dict_resp = session.get(config.public_key_url, cookies=cookies)
        cookies.update(public_key_dict_resp.cookies)
        public_key_dict = public_key_dict_resp.json()
    except Exception as e:
        logging.error(f"Failed to get public key: {str(e)}")
        custom_abort(-1, '获取登录密钥失败，请稍后再试!')

    post_data = {
        'authcode': '',
        '_eventId': 'submit',
        'execution': execution,
        'username': name,
        # 获取rsa加密的密码
        'password': Encrypt(public_key_dict["exponent"], public_key_dict["modulus"]).encrypt(passwd[::-1])
    }
    return cookies, post_data


# 判断登录结果,更新cookies并返回
def check_login(cookies: RequestsCookieJar, login_response: Response):
    if login_response.status_code == 302 and config.up_url in login_response.headers.get('location'):
        custom_abort(-3, '请修改密码!')
    cookies.update(login_response.cookies)
    if login_response.status_code == 302:
        login_response, cookies = follow_link(login_response.cookies, login_response.headers.get('location'))
    
    # 尝试使用不同的编码方式解码内容
    login_response_html = None
    for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
        try:
            login_response_html = login_response.content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
            
    if not login_response_html:
        custom_abort(-1, '无法解码登录响应内容')
        
    if login_response_html.find("用户名或密码错误") != -1:
        custom_abort(-3, '账号或密码错误!')
    elif login_response_html.find("完成，进入门户") != -1:
        custom_abort(-3, '未绑定手机号!')
    elif login_response_html.find("当前账号无权登录") != -1:
        custom_abort(-3, '无权登录此账号!')
    elif login_response_html.find("统一身份认证") != -1:
        custom_abort(-3, '未知登录错误!')
    return cookies
