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
└── templates/               # Web界面模板
    └── index.html           # 管理后台界面
```

