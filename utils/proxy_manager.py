#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import logging
import random
import time
import requests
from typing import Dict, List, Optional, Union, Any

from global_config import proxy_list, proxy_rotation_policy, proxy_request_timeout, proxy_retry_delay

class ProxyManager:
    """
    代理管理器
    用于管理多个代理服务器并提供代理轮询功能
    """
    
    def __init__(self):
        """
        初始化代理管理器
        """
        # 格式化代理列表，将配置转换为请求库可用的格式
        self.formatted_proxies = self._format_proxies(proxy_list)
        
        # 检查代理列表是否为空
        if not self.formatted_proxies:
            logging.warning("警告：代理列表为空，请求将使用直接连接")
        else:
            logging.info(f"已加载 {len(self.formatted_proxies)} 个代理服务器")
        
        # 根据轮询策略创建代理迭代器
        if proxy_rotation_policy == 'random':
            # 随机选择策略
            self.proxy_iterator = self._random_proxy_generator()
        else:
            # 默认轮询策略
            self.proxy_iterator = itertools.cycle(self.formatted_proxies) if self.formatted_proxies else None

    def _format_proxies(self, proxy_configs: List[Dict[str, str]]) -> List[Dict[str, Dict[str, str]]]:
        """
        格式化代理配置，转换为requests库可用的格式
        
        Args:
            proxy_configs: 代理配置列表
            
        Returns:
            格式化后的代理列表
        """
        formatted_list = []
        
        for config in proxy_configs:
            if not config or 'url' not in config or not config['url']:
                continue
                
            proxy_type = config.get('type', 'http').lower()
            proxy_url = config['url']
            
            # 处理带认证的代理
            if 'username' in config and 'password' in config and config['username'] and config['password']:
                auth_url = f"{proxy_type}://{config['username']}:{config['password']}@{proxy_url}"
            else:
                auth_url = f"{proxy_type}://{proxy_url}"
                
            # 构建代理配置（同时支持http和https）
            proxy_dict = {
                "http": auth_url,
                "https": auth_url
            }
            
            formatted_list.append(proxy_dict)
            
        return formatted_list
        
    def _random_proxy_generator(self):
        """
        随机代理生成器
        
        Returns:
            随机选择的代理
        """
        while True:
            yield random.choice(self.formatted_proxies) if self.formatted_proxies else None
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        获取下一个代理服务器
        
        Returns:
            代理配置字典，如果没有可用代理则返回None
        """
        if not self.proxy_iterator:
            return None
            
        return next(self.proxy_iterator)
    
    def make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        使用代理轮询发出请求，并在失败时自动重试下一个代理
        
        Args:
            method: HTTP请求方法 (get, post等)
            url: 目标URL
            **kwargs: 其他传递给requests.request的参数
            
        Returns:
            请求响应对象
            
        Raises:
            requests.RequestException: 所有代理都失败时抛出最后一个异常
        """
        # 如果没有代理，直接发出请求
        if not self.formatted_proxies:
            return requests.request(method, url, **kwargs)
        
        # 设置超时时间，避免请求卡死
        timeout = kwargs.pop('timeout', proxy_request_timeout)
        
        last_exception = None
        tried_proxies = set()
        
        # 尝试所有代理，直到请求成功或所有代理都失败
        while len(tried_proxies) < len(self.formatted_proxies):
            current_proxy = self.get_next_proxy()
            
            # 跟踪已尝试过的代理
            proxy_key = str(current_proxy)
            if proxy_key in tried_proxies:
                continue
            tried_proxies.add(proxy_key)
            
            try:
                logging.debug(f"正在使用代理 {current_proxy} 访问 {url}")
                
                # 发出请求
                response = requests.request(
                    method, 
                    url, 
                    proxies=current_proxy, 
                    timeout=timeout, 
                    **kwargs
                )
                
                # 检查响应状态
                response.raise_for_status()
                
                logging.debug(f"使用代理 {current_proxy} 成功访问 {url}")
                return response
                
            except (
                requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError
            ) as e:
                # 记录代理失败
                logging.warning(f"代理 {current_proxy} 失败: {type(e).__name__} - {str(e)}")
                last_exception = e
                
                # 短暂延迟后尝试下一个代理
                if proxy_retry_delay > 0:
                    time.sleep(proxy_retry_delay)
        
        # 所有代理都失败，抛出最后一个异常
        if last_exception:
            raise last_exception
            
        # 如果没有代理或所有代理都失败但没有异常，直接使用无代理请求
        logging.warning("所有代理均已失败，尝试直接连接")
        return requests.request(method, url, **kwargs)
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """
        使用GET方法发送请求
        
        Args:
            url: 目标URL
            **kwargs: 其他传递给requests.request的参数
            
        Returns:
            请求响应对象
        """
        return self.make_request('get', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """
        使用POST方法发送请求
        
        Args:
            url: 目标URL
            **kwargs: 其他传递给requests.request的参数
            
        Returns:
            请求响应对象
        """
        return self.make_request('post', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """
        使用PUT方法发送请求
        
        Args:
            url: 目标URL
            **kwargs: 其他传递给requests.request的参数
            
        Returns:
            请求响应对象
        """
        return self.make_request('put', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """
        使用DELETE方法发送请求
        
        Args:
            url: 目标URL
            **kwargs: 其他传递给requests.request的参数
            
        Returns:
            请求响应对象
        """
        return self.make_request('delete', url, **kwargs)


# 创建全局代理管理器实例
proxy_manager = ProxyManager()
