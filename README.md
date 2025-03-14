# wakeNUC-Backend

这是一个基于Flask的后端服务项目，主要用于处理校园网络相关的服务和任务调度。

## 项目描述

本项目是一个基于Python Flask框架开发的后端服务系统，提供了一系列与校园网络资源访问相关的功能。项目采用模块化设计，支持插件扩展，并包含定时任务调度功能。

## 主要特性

- 模块化的插件系统
- 定时任务调度
- 全局异常处理
- 响应压缩
- 数据库支持（SQLite/MySQL）
- 代理支持
- 日志系统
- 安全的错误处理机制

## 技术栈

- **Web框架**: Flask
- **WSGI服务器**: Gevent
- **数据库**: SQLAlchemy (支持SQLite和MySQL)
- **任务调度**: APScheduler
- **网络请求**: Requests
- **HTML解析**: BeautifulSoup4, html5lib
- **数据压缩**: Flask-Compress
- **加密工具**: PyCryptodome, cryptography
- **云服务**: 腾讯云SDK
- **其他工具**: Redis, icalendar等

## 安装说明

1. 克隆项目到本地：
```bash
git clone https://github.com/Alpenl/wakeNUC-Backend.git
cd wakeNUC-Backend
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置数据库：
- 默认使用SQLite内存数据库
- 如需使用MySQL，请修改`index.py`中的数据库配置

## 使用说明

### 开发环境启动

```bash
python index.py
```
服务器将在 http://0.0.0.0:8080 启动

### Docker部署

1. 构建镜像：
```bash
docker build -t wakenuc-backend .
```

2. 运行容器：
```bash
docker run -p 8080:8080 wakenuc-backend
```

## 项目结构

```
wakenuc-backend/
├── index.py           # 主入口文件
├── global_config.py   # 全局配置
├── models/           # 数据模型
├── plugins_v3/       # 插件目录
├── tasks/           # 定时任务
├── utils/           # 工具函数
├── startup/         # 启动脚本
└── log/            # 日志文件
```

## 注意事项

- 确保正确配置代理设置（如果需要访问校内网络）
- 注意处理好数据库连接配置
- 确保所需的端口（默认8080）未被占用

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。

## 许可证

本项目采用 [GNU通用公共许可证v3.0](https://github.com/Alpenl/wakeNUC-Backend/blob/main/LICENSE) 开源许可证。

Copyright (c) 2025 Alpen

本程序是自由软件：你可以根据自由软件基金会发布的 GNU 通用公共许可证的条款，即许可证的第3版或（您选择的）任何后来的版本重新发布它和/或修改它。

本程序的发布是希望它能够有用，但没有任何担保；甚至没有适合特定目的的隐含担保。更多细节请参见GNU通用公共许可证。

你应该已经收到一份GNU通用公共许可证的副本。如果没有，请参阅 <https://www.gnu.org/licenses/>。
