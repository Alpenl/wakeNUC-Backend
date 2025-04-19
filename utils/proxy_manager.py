#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import requests
import os
from typing import Dict, List, Optional, Union, Any

from global_config import proxy_list, proxy_rotation_policy, proxy_request_timeout, proxy_retry_delay

class ProxyManager:
    """
    代理管理器
    用于管理多个代理服务器并提供简单的代理切换功能
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
        
        # 当前使用的代理索引
        self.current_proxy_index = 0
        
        # 设置系统代理（设置为第一个代理）
        self._set_system_proxy(0)
    
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
    
    def _set_system_proxy(self, index: int) -> bool:
        """
        设置系统代理环境变量
        
        Args:
            index: 代理在列表中的索引
            
        Returns:
            是否成功设置
        """
        if not self.formatted_proxies or index >= len(self.formatted_proxies):
            # 清除系统代理
            if "http_proxy" in os.environ:
                del os.environ["http_proxy"]
            if "https_proxy" in os.environ:
                del os.environ["https_proxy"]
            return False
        
        # 获取指定索引的代理
        proxy = self.formatted_proxies[index]
        
        # 从代理字典中提取URL(去掉协议前缀)
        proxy_url = proxy.get("http", "")
        if "://" in proxy_url:
            proxy_url = proxy_url.split("://", 1)[1]
        
        # 提取代理类型
        proxy_type = "http"  # 默认类型
        for p_type in ["http", "https", "socks5", "socks4"]:
            if p_type in proxy.get("http", ""):
                proxy_type = p_type
                break
        
        # 设置系统代理环境变量
        os.environ["http_proxy"] = f"{proxy_type}://{proxy_url}"
        os.environ["https_proxy"] = f"{proxy_type}://{proxy_url}"
        
        # 更新当前使用的代理索引
        self.current_proxy_index = index
        
        logging.info(f"已将系统代理设置为 #{index+1}: {proxy_type}://{proxy_url}")
        return True
    
    def switch_to_next_proxy(self) -> bool:
        """
        切换到下一个代理
        
        Returns:
            是否成功切换
        """
        if not self.formatted_proxies:
            return False
        
        # 计算下一个代理的索引
        next_index = (self.current_proxy_index + 1) % len(self.formatted_proxies)
        
        # 设置为系统代理
        success = self._set_system_proxy(next_index)
        
        return success
    
    def use_proxy(self, index: int) -> bool:
        """
        使用指定索引的代理
        
        Args:
            index: 代理在列表中的索引
            
        Returns:
            是否成功切换
        """
        if not self.formatted_proxies or index >= len(self.formatted_proxies):
            return False
        
        return self._set_system_proxy(index)
    
    def make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        使用当前系统代理发送请求
        
        Args:
            method: HTTP请求方法 (get, post等)
            url: 目标URL
            **kwargs: 其他传递给requests.request的参数
            
        Returns:
            请求响应对象
            
        Raises:
            requests.RequestException: 请求失败时抛出异常
        """
        # 如果没有代理，直接发出请求
        if not self.formatted_proxies:
            return requests.request(method, url, **kwargs)
        
        # 设置超时时间，避免请求卡死
        timeout = kwargs.pop('timeout', proxy_request_timeout)
        
        # 获取当前代理
        current_proxy = self.formatted_proxies[self.current_proxy_index]
        
        # 发送请求
        response = requests.request(
            method, 
            url, 
            proxies=current_proxy, 
            timeout=timeout, 
            **kwargs
        )
        
        return response
    
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
