# RSS to Feishu 项目

将RSS订阅内容自动同步到飞书群聊的Python应用

## 主要功能

- 定时抓取配置的RSS订阅源
- 解析并格式化文章内容
- 通过飞书Webhook推送新内容到群聊
- 简单的Web管理界面

## 环境要求

- Python 3.8+
- pip 包管理工具

## 安装教程

1. 克隆仓库
```bash
git clone https://github.com/Qianxia666/rss-to-feishu.git
cd rss-to-feishu
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行程序
```bash
python rss_to_feishu.py
```


4. 配置环境变量  
进入网页后填写以下配置：
```ini
你的飞书机器人Webhook地址
要监控的RSS订阅地址
检查间隔
```

## 使用说明

1. 访问管理界面 `http://localhost:5000`
2. 在飞书群聊中添加机器人并获取Webhook地址
3. 添加需要监控的RSS订阅地址
4. 系统将自动按指定间隔检查更新

## 项目结构
```
.
├── requirements.txt         # 依赖清单
├── rss_to_feishu.py         # 主程序入口
├── converter.py             # 内容格式转换器
├── Dockerfile               # Docker镜像构建文件
├── docker-compose.yml       # Docker Compose配置文件
├── startapp.sh              # 一键部署脚本
└── templates/               # Web界面模板
    └── index.html           # 管理后台界面
```

## Docker部署

本项目提供了完整的Docker部署支持，推荐使用Docker方式部署，可以避免环境依赖问题。

> **⚠️ 注意：** Docker构建镜像方式尚未经过完整测试，请谨慎使用。如遇问题，请提交Issue或回退到标准部署方式。

### 快速部署（推荐）

项目提供了一键部署脚本，可以自动完成环境检查、构建镜像和启动服务的全过程：

1. 赋予脚本执行权限
```bash
chmod +x startapp.sh
```

2. 运行部署脚本
```bash
./startapp.sh
```

脚本会自动检查Docker环境，准备配置文件，构建镜像并启动服务。

### 使用脚本管理服务

startapp.sh脚本支持多种命令参数，可以方便地管理服务：

```bash
./startapp.sh start     # 启动服务
./startapp.sh stop      # 停止服务
./startapp.sh restart   # 重启服务
./startapp.sh status    # 查看服务状态
./startapp.sh logs      # 查看服务日志
./startapp.sh update    # 更新代码并重启服务
```

### 手动Docker部署

如果需要手动部署，可以按照以下步骤操作：

1. 构建Docker镜像
```bash
docker build -t rss-to-feishu .
```

2. 运行Docker容器
```bash
docker run -d -p 5000:5000 \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/sent_entries.json:/app/sent_entries.json \
  -v $(pwd)/rss_feishu.log:/app/rss_feishu.log \
  --name rss-to-feishu \
  --restart unless-stopped \
  rss-to-feishu
```

### 使用Docker Compose部署

也可以使用Docker Compose进行更简便的部署：

1. 启动服务
```bash
docker-compose up -d
```

2. 查看日志
```bash
docker-compose logs -f
```

3. 停止服务
```bash
docker-compose down
```

4. 重新构建并启动服务（代码更新后）
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 数据持久化

服务通过卷挂载实现了数据持久化，包括：
- `config.json` - 配置文件
- `sent_entries.json` - 已发送的记录
- `rss_feishu.log` - 日志文件

即使容器重启或重建，这些数据也会保持不变。

### 注意事项

- 首次启动后，请访问 `http://服务器IP:5000` 完成配置
- 确保防火墙已开放5000端口（如果需要从外部访问）
- 如果修改了代码，需要重新构建镜像才能生效

