import feedparser
from typing import Dict, Any

def convert_to_feishu_format(entry: Dict[str, Any]) -> Dict[str, Any]:
    """将RSS条目转换为飞书消息格式"""
    content = []
    
    # 处理描述内容
    if entry.get('description'):
        content.append([{
            "tag": "text",
            "text": entry['description']
        }])
    
    # 添加链接
    if entry.get('link'):
        content.append([{
            "tag": "a",
            "text": "点击查看",
            "href": entry['link']
        }])
    
    return {
        "msg_type": "post",
        "content": {
            "post": {
                "zh-CN": {
                    "title": entry.get('title', '无标题'),
                    "content": content
                }
            }
        }
    }

def parse_rss_feed(url: str) -> list:
    """解析RSS feed并返回飞书格式消息列表"""
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            raise ValueError(f"RSS解析错误: {feed.bozo_exception}")
        
        return [convert_to_feishu_format(entry) for entry in feed.entries]
    except Exception as e:
        raise ValueError(f"处理RSS时出错: {str(e)}")
