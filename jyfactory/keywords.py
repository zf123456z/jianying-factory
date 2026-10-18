#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动从文案里提取爆款关键词
这些关键词在字幕里会自动变红加粗，抓眼球
"""
import re

# 爆款关键词词典
HOT_WORDS = [
    "三步法", "AI获客", "GEO", "生成式引擎优化", "2024", "普通人",
    "赚钱", "副业", "流量", "转化", "免费", "干货", "避坑",
    "第一步", "第二步", "第三步", "记住", "重点", "核心",
    "别再", "一定要", "立刻", "马上", "评论区", "点赞",
    "免费领", "领取", "私信", "关注", "转发",
]

def extract_keywords(script: str, max_keywords: int = 5):
    """
    从文案里提取需要高亮的关键词
    :param script: 口播文案
    :param max_keywords: 最多提取几个关键词
    :return: 关键词列表
    """
    found = []
    for word in HOT_WORDS:
        if word in script and word not in found:
            found.append(word)
        if len(found) >= max_keywords:
            break

    # 如果词典里没找到，就提取长度4-6字的名词性短语（简单版）
    if len(found) < 3:
        # 找所有引号里的词
        quotes = re.findall(r'[""「](.*?)[""」]', script)
        for q in quotes:
            if len(q) >= 2 and q not in found:
                found.append(q)
            if len(found) >= max_keywords:
                break

    print(f"🔍 提取到高亮关键词：{found}")
    return found


if __name__ == "__main__":
    # 测试
    script = "那怎么做？三步。第一步，反向问AI。第二步，锁定AI的参考源。第三步，按AI的审美发内容。这套逻辑做完，能帮你解决大部分获客问题。如果你是品牌公司，想做但不知道从哪下手，评论区打\"结构图\"，我免费发你一套完整落地图。"
    kws = extract_keywords(script)
    print(f"关键词：{kws}")
