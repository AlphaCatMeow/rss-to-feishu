from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import json
import time
import feedparser
import requests
import logging
from datetime import datetime
import os
from flask_cors import CORS

# 初始化日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rss_feishu.log'),
        logging.StreamHandler()
    ]
)

# 已发送记录文件
SENT_ENTRIES_FILE = 'sent_entries.json'

def load_sent_entries():
    if not os.path.exists(SENT_ENTRIES_FILE):
        return []
    try:
        with open(SENT_ENTRIES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载已发送记录失败: {e}")
        return []

def save_sent_entries(entries):
    try:
        with open(SENT_ENTRIES_FILE, 'w') as f:
            json.dump(entries, f)
    except Exception as e:
        logging.error(f"保存已发送记录失败: {e}")

app = Flask(__name__)
CORS(app)

CONFIG_FILE = 'config.json'
scheduler = BackgroundScheduler()

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def fetch_and_send():
    config = load_config()
    if not config:
        logging.warning("未找到有效配置")
        return
    
    try:
        feed = feedparser.parse(config['rss_url'])
        if feed.entries:
            sent_entries = load_sent_entries()
            new_entries = []
            
            for entry in feed.entries:
                entry_id = entry.get('id', entry.link)
                if entry_id not in sent_entries:
                    message = {
                        "msg_type": "interactive",
                        "card": {
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "content": f"**{entry.title}**\n{entry.link}",
                                    "tag": "lark_md"
                                }
                            }]
                        }
                    }
                    try:
                        response = requests.post(config['webhook_url'], json=message, timeout=10)
                        response.raise_for_status()
                        sent_entries.append(entry_id)
                        new_entries.append(entry_id)
                        logging.info(f"成功推送: {entry.title}")
                    except Exception as e:
                        logging.error(f"推送失败: {entry.title} - {str(e)}")
            
            if new_entries:
                # 保留最近100条记录防止文件过大
                sent_entries = sent_entries[-100:]
                save_sent_entries(sent_entries)
                logging.info(f"本次推送完成，新增{len(new_entries)}条记录")
            else:
                logging.info("没有新内容需要推送")
                
    except Exception as e:
        logging.error(f"RSS解析失败: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config', methods=['POST'])
def handle_config():
    data = request.json
    if not all(key in data for key in ('rss_url', 'interval', 'webhook_url')):
        return jsonify({'error': 'Missing parameters'}), 400
        
    config = {
        'rss_url': data['rss_url'],
        'interval': int(data['interval']),
        'webhook_url': data['webhook_url']
    }
    save_config(config)
    
    # 重启定时任务
    scheduler.remove_all_jobs()
    scheduler.add_job(fetch_and_send, 'interval', minutes=config['interval'])
    
    if not scheduler.running:
        scheduler.start()
    
    return jsonify({'message': '配置已保存，推送服务已启动'})

if __name__ == '__main__':
    # 初始化时加载配置并启动任务
    config = load_config()
    if config:
        scheduler.add_job(fetch_and_send, 'interval', minutes=config.get('interval', 10))
        logging.info("已加载现有配置启动定时任务")
    
    scheduler.start()
    logging.info(f"调度器已启动，任务列表: {scheduler.get_jobs()}")
    
    # 启动Flask应用时关闭调试模式避免重复执行
    app.run(debug=False, port=5000)
