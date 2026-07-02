#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信机器人推送模块
将每日 AI 资讯日报推送到企业微信群机器人。
"""

import json
import os
import requests
import time
from datetime import datetime


# ============================================================
# 配置
# ============================================================
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL", "")
MAX_RETRIES = 2
RETRY_DELAY = 2  # 秒


# ============================================================
# 消息构建
# ============================================================
def _build_markdown_content(report):
    """
    将日报报告转换为企业微信 Markdown 格式。
    企业微信限制单条消息 4096 字节，需严格控制长度。
    """
    date_str = report.get("date", datetime.now().strftime("%Y-%m-%d"))
    items = report.get("items", [])

    # 紧凑版头
    header = f"## 🤖 AI资讯日报 {date_str}  |  {len(items)}条精选"

    # 按分类展示，每行尽量精简
    emoji_map = {"技术动态": "🔧", "AI论文": "📄", "新产品": "🚀", "行业热点": "📰"}
    body_lines = []
    seen = set()
    for item in items:
        cat = item.get("category", "资讯")
        if cat not in seen:
            emoji = emoji_map.get(cat, "📌")
            body_lines.append(f"\n**{emoji} {cat}**")
            seen.add(cat)

        title = item.get("title_cn") or item.get("title", "无标题")
        url = item.get("url", "")
        comment = item.get("comment", "")

        # 标题截断至 45 字符，URL 必填，锐评截断至 35 字符
        title_short = _truncate(title, 45)
        line = f"- [{title_short}]({url})"
        if comment:
            line += f"  💬{_truncate(comment, 35)}"
        body_lines.append(line)

    # 页脚
    footer = "\n📡 GitHub · arXiv · TechCrunch · HN  |  [官网](https://theyun63-yvette.github.io/ai-daily-digest/)"

    # 组装并截断到 4000 字节（留 96 字节缓冲）
    content = header + "\n".join(body_lines) + footer
    if len(content.encode("utf-8")) > 4000:
        # 逐行丢弃直到符合长度
        while len(content.encode("utf-8")) > 4000 and len(body_lines) > 2:
            body_lines.pop()
            content = header + "\n".join(body_lines) + "\n...（已截断）" + footer

    return content


def _truncate(text, max_len):
    """截断文本，超长加省略号"""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"


# ============================================================
# 推送
# ============================================================
def send_to_wecom(report):
    """
    将日报推送到企业微信群机器人。

    Args:
        report: generate_daily_report() 返回的日报 dict

    Returns:
        bool: 推送成功返回 True，失败返回 False
    """
    if not WECOM_WEBHOOK_URL:
        print("[WARN] 未配置 WECOM_WEBHOOK_URL 环境变量，跳过企业微信推送")
        print("       请在 .env 文件中设置: WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx")
        return False

    content = _build_markdown_content(report)

    # 企业微信 Markdown 消息体
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }

    # 带重试的发送
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.post(
                WECOM_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )

            if resp.status_code == 200:
                result = resp.json()
                if result.get("errcode") == 0:
                    print("✅ 企业微信推送成功")
                    return True
                else:
                    print(f"[ERROR] 企业微信 API 返回错误: {result}")
            else:
                print(f"[ERROR] 企业微信推送 HTTP {resp.status_code}: {resp.text[:300]}")

        except requests.exceptions.Timeout:
            print(f"[ERROR] 企业微信推送超时 (attempt {attempt + 1})")
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] 企业微信推送连接失败 (attempt {attempt + 1})")
        except Exception as e:
            print(f"[ERROR] 企业微信推送异常 (attempt {attempt + 1}): {e}")

        if attempt < MAX_RETRIES:
            print(f"[INFO] {RETRY_DELAY}s 后重试...")
            time.sleep(RETRY_DELAY)

    print("[ERROR] 企业微信推送最终失败，已达最大重试次数")
    return False
