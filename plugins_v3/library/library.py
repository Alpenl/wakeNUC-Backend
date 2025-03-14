import re
import traceback
from urllib.parse import quote

import bs4
import requests
from flask import request
from gevent.pool import Pool

from utils.decorators.cache import cache
from utils.decorators.check_sign import check_sign
from utils.decorators.request_limit import request_limit
from utils.exceptions import custom_abort
from utils.gol import global_values
from utils.session import session
from . import api, config
import logging

# 禁用SSL警告
requests.packages.urllib3.disable_warnings()


@api.route('/library/search/name/<string:keyword>', methods=['GET'])
@check_sign({'type', 'page'})  # 验证请求签名
@request_limit()               # 限制请求频率
@cache({'type', 'page'}, 180)  # 缓存结果180秒
def handle_library_search_by_name(keyword: str):
    """
    根据书名关键词搜索图书
    
    路径参数:
    - keyword: 搜索关键词
    
    查询参数:
    - type: 搜索类型，默认为'正题名'
    - page: 页码，默认为1
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 包含搜索结果的数据对象
      - records: 总记录数
      - page: 当前页码
      - recordsPerPage: 每页记录数
      - list: 图书列表
    """
    # 获取请求参数
    book_type = request.args.get('type', '正题名')
    page = request.args.get('page', '1')
    
    # 构建搜索URL
    url = 'http://222.31.39.3:8080/pft/wxjs/bk_s_Q_fillpage.asp?q=%s=[[*%s*]]' \
          '&nmaxcount=&nSetPageSize=10&orderby=&Research=1&page=%s&opt=1' % (quote(book_type), keyword, page)
    
    # 发送请求获取搜索结果页面
    response = session.get(url)
    content = None
    for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
        try:
            content = response.content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
            
    if not content:
        logging.error("无法解码图书搜索响应内容")
        custom_abort(-1, '图书搜索服务暂时无法访问，请稍后再试!')
    
    # 解析图书ID列表和总记录数
    re_book_ids = re.findall(r"ShowItem\('([0-9]*)'\)", content)
    records_group = re.search('共([0-9]*)条记录', content)
    if not records_group:
        custom_abort(-6, '无结果')
    records = records_group.group(1)
    
    # 使用协程池并行获取每本图书的详细信息
    pool = Pool(10)
    book_list = pool.map(book_detail, re_book_ids)
    
    # 返回搜索结果
    return {
        'code': 0,
        'data': {
            'records': records,          # 总记录数
            'page': page,                # 当前页码
            'recordsPerPage': len(book_list),  # 当前页记录数
            'list': book_list            # 图书列表
        }
    }


@api.route('/library/search/isbn/<string:isbn>', methods=['GET'])
@check_sign({'page'})         # 验证请求签名
@request_limit()              # 限制请求频率
@cache({'page'}, 180)         # 缓存结果180秒
def handle_library_search_by_isbn(isbn: str):
    """
    根据ISBN编号搜索图书
    
    路径参数:
    - isbn: 图书ISBN编号
    
    查询参数:
    - page: 页码，默认为1
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 包含搜索结果的数据对象
      - records: 总记录数
      - page: 当前页码
      - recordsPerPage: 每页记录数
      - list: 图书列表
    """
    # 获取请求参数
    page = request.args.get('page', '1')
    
    # 验证ISBN格式
    if len(isbn) != 13 and len(isbn) != 10:
        custom_abort(-6, '无效的 ISBN 编号')
    
    # 格式化ISBN编号（添加连字符）
    if len(isbn) == 10:
        isbn = isbn[:1] + '-' + isbn[1:5] + '-' + isbn[5:9] + '-' + isbn[9:]
    else:
        isbn = isbn[:3] + '-' + isbn[3:4] + '-' + isbn[4:8] + '-' + isbn[8:12] + '-' + isbn[12:]
    
    # 构建搜索URL
    url = 'http://222.31.39.3:8080/pft/showmarc/table.asp?q=标准编号=[[%s*]]' \
          '&nmaxcount=&nSetPageSize=10&orderby=&Research=1&page=%s&opt=1' % (quote(isbn), page)
    
    # 发送请求获取搜索结果页面
    content = session.get(url).content.decode('utf-8')
    
    # 解析图书ID列表和总记录数
    re_book_ids = re.findall(r"ShowItem\('([0-9]*)'\)", content)
    records_group = re.search('共([0-9]*)条记录', content)
    if not records_group:
        custom_abort(-6, '无结果')
    records = records_group.group(1)
    
    # 使用协程池并行获取每本图书的详细信息
    pool = Pool(10)
    book_list = pool.map(book_detail, re_book_ids)
    
    # 返回搜索结果
    return {
        'code': 0,
        'data': {
            'records': records,          # 总记录数
            'page': page,                # 当前页码
            'recordsPerPage': len(book_list),  # 当前页记录数
            'list': book_list            # 图书列表
        }
    }


@api.route('/library/books/<string:book_id>', methods=['GET'])
@check_sign(set())            # 验证请求签名
@request_limit()              # 限制请求频率
@cache(set(), 180)            # 缓存结果180秒
def get_book_available_detail(book_id: str):
    """
    获取指定图书的馆藏信息
    
    路径参数:
    - book_id: 图书ID
    
    返回数据:
    - code: 状态码，0表示成功
    - data: 图书馆藏信息列表，包含索书号、条码号、馆藏地点和借阅状态
    """
    # 构建图书馆藏信息URL
    url = "http://222.31.39.3:8080/pft/showmarc/showbookitems.asp?nTmpKzh=%s" % book_id
    
    # 发送请求获取图书馆藏信息页面
    content = session.get(url).content.decode("utf-8")
    
    # 解析HTML获取馆藏信息
    soups = bs4.BeautifulSoup(content, "html.parser")
    trs = soups.find_all("tr")
    detail_items = []
    
    # 提取每条馆藏信息
    for td in trs[1:]:
        tds = td.find_all("td")
        detail_items.append({
            "number": "".join(tds[1].text.split()),     # 索书号
            "barcode": "".join(tds[2].text.split()),    # 条码号
            "location": "".join(tds[3].text.split()),   # 馆藏地点
            "status": "".join(tds[4].text.split())      # 借阅状态
        })
    
    # 返回馆藏信息
    return {
        'code': 0,
        'data': detail_items
    }


def book_detail(book_id) -> dict:
    """
    获取图书的详细信息
    
    参数:
    - book_id: 图书ID
    
    返回:
    - 包含图书详细信息的字典
    """
    # 获取图书基本信息
    url = "http://222.31.39.3:8080/pft/showmarc/table.asp?nTmpKzh=%s" % book_id
    content = session.get(url).content
    soups = bs4.BeautifulSoup(content, "html.parser")
    details = soups.find(id="tabs-2").find_all("tr")
    
    # 获取图书可借阅数量
    url = "http://222.31.39.3:8080/pft/wxjs/BK_getKJFBS.asp"
    post_data = {"nkzh": book_id}
    response = session.post(url, data=post_data, headers={'Cookie': global_values.get_value('vpn_cookie')})
    
    # 尝试使用不同的编码方式解码内容
    content = None
    for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']:
        try:
            content = response.content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
            
    if not content:
        logging.error("无法解码图书可借阅数量响应内容")
        content = "0"  # 如果解码失败，默认为0
    
    # 初始化图书信息字典
    detail_dict = {"id": book_id, "available_books": content}
    
    # 解析MARC格式的图书信息
    for i in details:
        tds = i.find_all("td")
        # 解析ISBN和封面信息
        if tds[0].text.strip() == "010":
            info = tds[2].text.strip().split("@")
            for j in info:
                if len(j) < 1:
                    continue
                if j[0] == "a":
                    detail_dict["ISBN"] = j[1:]
                    detail_dict["cover_url"] = douban_book_cover(j[1:])  # 从豆瓣获取封面
        # 解析书名和作者信息
        elif tds[0].text.strip() == "200":
            info = tds[2].text.strip().split("@")
            for j in info:
                if len(j) < 1:
                    continue
                if j[0] == "a":
                    detail_dict["name"] = j[1:]  # 书名
                elif j[0] == "f":
                    detail_dict["author"] = j[1:]  # 作者
                elif j[0] == "g":
                    detail_dict["translator"] = j[1:]  # 译者
        # 解析出版信息
        elif tds[0].text.strip() == "210":
            info = tds[2].text.strip().split("@")
            for j in info:
                if len(j) < 1:
                    continue
                if j[0] == "c":
                    detail_dict["press"] = j[1:]  # 出版社
                elif j[0] == "d":
                    detail_dict["year"] = j[1:]  # 出版年份
                elif j[0] == "g":
                    detail_dict["translator"] = j[1:]  # 译者
        # 解析图书简介
        elif tds[0].text.strip() == "330":
            info = tds[2].text.strip().split("@")
            for j in info:
                if len(j) < 1:
                    continue
                if j[0] == "a":
                    detail_dict["introduction"] = j[1:]  # 图书简介
    
    # 如果没有封面，使用默认封面
    if "cover_url" not in detail_dict.keys():
        detail_dict[
            "cover_url"] = "https://img1.doubanio.com/f/shire/5522dd1f5b742d1e1394a17f44d590646b63871d/pics/book" \
                           "-default-lpic.gif"
    
    return detail_dict


def douban_book_cover(isbn: str) -> str:
    """
    从豆瓣API获取图书封面URL
    
    参数:
    - isbn: 图书ISBN编号
    
    返回:
    - 图书封面URL，获取失败时返回默认封面URL
    """
    # 默认封面URL
    default_url = "https://img1.doubanio.com/f/shire/5522dd1f5b742d1e1394a17f44d590646b63871d/pics/book-default-lpic" \
                  ".gif"
    try:
        # 请求豆瓣API获取图书信息
        response = session.get(
            "https://api.douban.com/v2/book/isbn/{}?apikey=054022eaeae0b00e0fc068c0c0a2102a".format(isbn),
            headers=config.douban_headers
        )
        # 检查请求是否成功
        if response.status_code != 200:
            return default_url
        # 从响应中提取封面URL
        return response.json().get('image', default_url)
    except requests.RequestException:
        # 请求异常时记录错误并返回默认封面
        traceback.print_exc()
        return default_url
