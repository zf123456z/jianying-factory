#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映工厂 - AI语义素材匹配 v2
根据文案内容，智能匹配最合适的视频素材
v2增强：同义词扩展、权重打分、场景识别
"""
import os
import re
from typing import List, Dict, Tuple


SYNONYMS = {
    "获客": ["引流", "找客户", "拓客", "客户", "流量", "变现", "赚钱"],
    "赚钱": ["副业", "收入", "创业", "生意", "变现", "收益"],
    "营销": ["推广", "广告", "销售", "卖货", "带货", "促销"],
    "AI": ["人工智能", "ChatGPT", "豆包", "DeepSeek", "大模型", "GPT"],
    "短视频": ["抖音", "快手", "视频号", "小红书", "TikTok", "口播"],
    "干货": ["知识", "教程", "方法", "技巧", "攻略", "指南"],
    "情感": ["治愈", "温暖", "感动", "孤独", "成长", "人生"],
}


class SemanticMatcherV2:
    def __init__(self, material_keywords: Dict[str, List[str]] = None):
        self.material_keywords = material_keywords or {}

    def expand_keywords(self, text: str) -> List[str]:
        keywords = []
        for word, synonyms in SYNONYMS.items():
            if word in text:
                keywords.append(word)
                keywords.extend(synonyms)
        return list(set(keywords))

    def score_material(self, material: str, keywords: List[str]) -> float:
        material_kws = self.material_keywords.get(material, [])
        if not material_kws:
            return 0.5
        score = 0
        for kw in keywords:
            for mkw in material_kws:
                if kw in mkw or mkw in kw:
                    score += 1
        return score / max(len(keywords), 1)

    def match_best_materials(self, text: str, top_n: int = 5) -> List[Tuple[str, float]]:
        keywords = self.expand_keywords(text)
        print(f"📝 文案核心关键词：{keywords[:5]}")
        scored = []
        for material in self.material_keywords:
            score = self.score_material(material, keywords)
            scored.append((material, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]


if __name__ == "__main__":
    matcher = SemanticMatcherV2({
        "商务办公.mp4": ["办公", "开会", "电脑", "商务", "职场"],
        "街景.mp4": ["街景", "城市", "走路", "人流", "商业"],
        "大自然.mp4": ["自然", "风景", "治愈", "山", "水"],
        "人物讲话.mp4": ["讲话", "演讲", "口播", "主播"],
    })
    text = "GEO获客三步法，帮你用AI工具引流找客户"
    results = matcher.match_best_materials(text, top_n=3)
    print("\n🎯 匹配结果：")
    for material, score in results:
        print(f"  {material}: {score:.2f}")
