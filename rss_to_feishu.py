from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import json
import time
import html
import sys
if sys.version_info >= (3, 11):
    sys.modules['cgi'] = type('cgi', (), {
        'parse_header': lambda header: (header, {}),
        'escape': html.escape
    })
import feedparser
import requests
import logging
from datetime import datetime
import os
from flask_cors import CORS
import uuid

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
        return {}
    try:
        with open(SENT_ENTRIES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载已发送记录失败: {e}")
        return {}

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
            config = json.load(f)
            # 兼容旧版本配置
            if isinstance(config, dict) and 'rss_url' in config and 'webhook_url' in config:
                # 转换旧版本配置为新格式
                old_config = config
                config = {
                    'webhook_url': old_config['webhook_url'],
                    'interval': old_config.get('interval', 60),
                    'sources': [{
                        'id': str(uuid.uuid4()),
                        'url': old_config['rss_url'],
                        'name': '默认RSS源'
                    }]
                }
                save_config(config)
            return config
    except FileNotFoundError:
        # 初始配置
        return {
            'webhook_url': '',
            'interval': 60,
            'sources': []
        }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def fetch_and_send():
    config = load_config()
    if not config or not config.get('webhook_url') or not config.get('sources'):
        logging.warning("未找到有效配置或RSS源为空")
        return
    
    sent_entries = load_sent_entries()
    webhook_url = config['webhook_url']
    
    for source in config['sources']:
        source_id = source['id']
        rss_url = source['url']
        source_name = source['name']
        
        if source_id not in sent_entries:
            sent_entries[source_id] = []
            
        try:
            feed = feedparser.parse(rss_url)
            if feed.entries:
                new_entries = []
                
                for entry in feed.entries:
                    entry_id = entry.get('id', entry.link)
                    if entry_id not in sent_entries[source_id]:
                        message = {
                            "msg_type": "interactive",
                            "card": {
                                "elements": [
                                    {
                                        "tag": "div",
                                        "text": {
                                            "content": f"**来源：{source_name}**",
                                            "tag": "lark_md"
                                        }
                                    },
                                    {
                                        "tag": "div",
                                        "text": {
                                            "content": f"**{entry.title}**\n{entry.link}",
                                            "tag": "lark_md"
                                        }
                                    }
                                ]
                            }
                        }
                        try:
                            response = requests.post(webhook_url, json=message, timeout=10)
                            response.raise_for_status()
                            sent_entries[source_id].append(entry_id)
                            new_entries.append(entry_id)
                            logging.info(f"成功推送[{source_name}]: {entry.title}")
                        except Exception as e:
                            logging.error(f"推送失败[{source_name}]: {entry.title} - {str(e)}")
                
                if new_entries:
                    # 保留最近100条记录防止文件过大
                    sent_entries[source_id] = sent_entries[source_id][-100:]
                    logging.info(f"源[{source_name}]推送完成，新增{len(new_entries)}条记录")
                else:
                    logging.info(f"源[{source_name}]没有新内容需要推送")
                    
        except Exception as e:
            logging.error(f"RSS源[{source_name}]解析失败: {str(e)}")
    
    save_sent_entries(sent_entries)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'GET':
        return jsonify(load_config())
        
    data = request.json
    if not all(key in data for key in ('webhook_url', 'interval', 'sources')):
        return jsonify({'error': '缺少必要参数'}), 400
        
    config = {
        'webhook_url': data['webhook_url'],
        'interval': int(data['interval']),
        'sources': data['sources']
    }
    save_config(config)
    
    # 重启定时任务
    scheduler.remove_all_jobs()
    scheduler.add_job(fetch_and_send, 'interval', minutes=config['interval'])
    
    if not scheduler.running:
        scheduler.start()
    
    return jsonify({'message': '配置已保存，推送服务已启动'})

@app.route('/sources', methods=['POST'])
def add_source():
    config = load_config()
    source = request.json
    
    if not source.get('url') or not source.get('name'):
        return jsonify({'error': '缺少必要参数'}), 400
    
    new_source = {
        'id': source.get('id', str(uuid.uuid4())),
        'url': source['url'],
        'name': source['name']
    }
    
    # 如果是更新现有的源
    if source.get('id'):
        for i, s in enumerate(config['sources']):
            if s['id'] == source['id']:
                config['sources'][i] = new_source
                break
        else:
            config['sources'].append(new_source)
    else:
        config['sources'].append(new_source)
    
    save_config(config)
    return jsonify({'message': '添加/更新RSS源成功', 'source': new_source})

@app.route('/sources/<source_id>', methods=['DELETE'])
def delete_source(source_id):
    config = load_config()
    original_length = len(config['sources'])
    config['sources'] = [s for s in config['sources'] if s['id'] != source_id]
    
    if len(config['sources']) == original_length:
        return jsonify({'error': '未找到指定的RSS源'}), 404
    
    save_config(config)
    
    # 删除该源的发送记录
    sent_entries = load_sent_entries()
    if source_id in sent_entries:
        del sent_entries[source_id]
        save_sent_entries(sent_entries)
    
    return jsonify({'message': '删除RSS源成功'})

if __name__ == '__main__':
    # 初始化时加载配置并启动任务
    config = load_config()
    if config and config.get('webhook_url') and config.get('sources'):
        scheduler.add_job(fetch_and_send, 'interval', minutes=config.get('interval', 60))
        logging.info("已加载现有配置启动定时任务")
    
    scheduler.start()
    logging.info(f"调度器已启动，任务列表: {scheduler.get_jobs()}")
    
    # 启动Flask应用时关闭调试模式避免重复执行
    app.run(debug=False, host='0.0.0.0', port=5000)
