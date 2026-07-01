#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日AI资讯爬虫 - 升级版 v2
自动从 RSS/API 抓取最新 AI 资讯，翻译为中文，生成犀利锐评，输出 JSON 日报

数据来源：
  - 技术动态: GitHub Trending (API)
  - AI论文:   arXiv (API)
  - 新产品:   TechCrunch / The Verge (RSS)
  - 行业热点: Hacker News via hnrss.org (RSS)
"""

import json
import re
import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path

# ============================================================
# 可选依赖：feedparser（更健壮的 RSS 解析）
# ============================================================
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("[WARN] feedparser 未安装，将使用 xml.etree 解析 RSS（兼容性较弱）")
    print("       建议: pip install feedparser")

# ============================================================
# 配置
# ============================================================
DATA_DIR = Path(__file__).parent.parent / "data"
DOCS_DATA_DIR = Path(__file__).parent.parent / "docs" / "data"
DATA_DIR.mkdir(exist_ok=True)
DOCS_DATA_DIR.mkdir(exist_ok=True)

# AI 关键词（用于筛选 AI 相关内容）
AI_KEYWORDS = [
    "AI", "LLM", "GPT", "Claude", "Gemini", "OpenAI", "Anthropic",
    "DeepMind", "Copilot", "ChatGPT", "artificial intelligence",
    "machine learning", "deep learning", "neural network",
    "transformer", "diffusion", "language model", "foundation model",
    "large language", "generative AI", "GenAI", "agent",
    "NVIDIA", "GPU", "chip", "LLaMA", "Mistral", "Stable Diffusion",
    "Midjourney", "DALL-E", "Sora", "vector database", "RAG",
    "fine-tuning", "prompt", "token", "inference"
]

# RSS 数据源
RSS_SOURCES_PRODUCT = [
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "type": "rss"
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "type": "rss"
    },
]

RSS_SOURCES_HOTSPOT = [
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage?count=30",
        "type": "rss"
    },
]


# ============================================================
# 工具函数
# ============================================================

def sanitize_text(text):
    """
    清理文本中的特殊字符，防止 JSON 解析错误。
    将 ASCII 双引号替换为中文书名号。
    """
    if not text:
        return text
    # 将成对的 ASCII 双引号替换为中文书名号「」
    text = re.sub(r'"([^"]*)"', r'「\1」', text)
    # 替换剩余的孤立双引号
    text = text.replace('"', "'")
    return text


def title_similarity(a, b):
    """计算两个标题的相似度 (0.0 ~ 1.0)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def is_ai_related(title, summary=""):
    """检查文章是否与 AI 相关"""
    combined = (title + " " + summary).lower()
    for kw in AI_KEYWORDS:
        if kw.lower() in combined:
            return True
    return False


def parse_rss_date(date_str):
    """解析 RSS 中的各种日期格式，返回 datetime 对象"""
    if not date_str:
        return None

    # 尝试多种常见格式
    formats = [
        # RFC 2822 (最常见)
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        # ISO 8601
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        # 其他
        "%a, %d %b %Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue

    # feedparser 返回的是 struct_time 元组，这里做 fallback
    if isinstance(date_str, time.struct_time):
        try:
            return datetime.fromtimestamp(time.mktime(date_str), tz=timezone.utc)
        except Exception:
            return None

    return None


def filter_last_7_days(entries):
    """只保留最近 7 天内的条目"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    filtered = []
    for entry in entries:
        pub_date = entry.get("published_parsed") or entry.get("date")
        if pub_date and isinstance(pub_date, datetime):
            if pub_date.replace(tzinfo=timezone.utc) >= cutoff:
                filtered.append(entry)
        else:
            # 无法解析日期时保留该条目（不过滤）
            filtered.append(entry)
    return filtered


def deduplicate_entries(entries, threshold=0.75):
    """根据标题相似度去重（保留先出现的条目）"""
    if not entries:
        return entries
    result = []
    for entry in entries:
        is_dup = False
        for existing in result:
            sim = title_similarity(entry.get("title", ""),
                                   existing.get("title", ""))
            if sim >= threshold:
                is_dup = True
                break
        if not is_dup:
            result.append(entry)
    return result


# ============================================================
# RSS 抓取
# ============================================================

def fetch_rss_feed(source_name, url, max_items=30):
    """
    从 RSS/Atom feed 抓取条目。
    优先使用 feedparser，fallback 到 xml.etree。
    返回 dict 列表，每个 dict 包含 title, summary, url, date, source。
    """
    entries = []

    try:
        if HAS_FEEDPARSER:
            entries = _fetch_rss_with_feedparser(source_name, url, max_items)
        else:
            entries = _fetch_rss_with_etree(source_name, url, max_items)
    except Exception as e:
        print(f"[ERROR] RSS 抓取失败 ({source_name}): {e}")

    return entries


def _fetch_rss_with_feedparser(source_name, url, max_items):
    """使用 feedparser 库解析 RSS/Atom"""
    entries = []
    feed = feedparser.parse(url)

    if feed.bozo and not feed.entries:
        print(f"[WARN] {source_name} RSS 解析警告: {feed.bozo_exception}")
        return entries

    for item in feed.entries[:max_items]:
        title = item.get("title", "").strip()
        summary = item.get("summary", "") or item.get("description", "")
        # 清理 HTML 标签
        summary = re.sub(r"<[^>]+>", " ", summary).strip()
        summary = re.sub(r"\s+", " ", summary)[:500]

        link = item.get("link", "")
        # 有些 feed 的 link 是 dict
        if isinstance(link, dict):
            link = link.get("href", "")

        pub_date = None
        if hasattr(item, "published_parsed") and item.published_parsed:
            try:
                pub_date = datetime.fromtimestamp(
                    time.mktime(item.published_parsed), tz=timezone.utc
                )
            except Exception:
                pub_date = datetime.now(timezone.utc)

        if not pub_date:
            pub_date = datetime.now(timezone.utc)

        entries.append({
            "title": title,
            "summary": summary[:500],
            "url": link,
            "date": pub_date,
            "source": source_name,
        })

    print(f"[OK] {source_name}: 获取到 {len(entries)} 条")
    return entries


def _fetch_rss_with_etree(source_name, url, max_items):
    """使用 xml.etree.ElementTree 解析 RSS 2.0 / Atom（fallback）"""
    entries = []
    resp = requests.get(url, timeout=15, headers={
        "User-Agent": "Mozilla/5.0 (compatible; AI-Daily-Digest/2.0)"
    })
    resp.raise_for_status()

    # 处理可能的编码问题
    content = resp.content
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        # 尝试清理后再解析
        content = resp.text.encode("utf-8", errors="replace")
        root = ET.fromstring(content)

    # 自动检测 RSS 2.0 vs Atom
    ns = {}
    tag_root = root.tag.lower()

    if "rss" in tag_root:
        # RSS 2.0
        items = root.findall(".//item")
        for item in items[:max_items]:
            title = _get_xml_text(item, "title")
            summary = _get_xml_text(item, "description")
            summary = re.sub(r"<[^>]+>", " ", summary).strip()
            summary = re.sub(r"\s+", " ", summary)[:500]
            link = _get_xml_text(item, "link")
            pub_date_str = _get_xml_text(item, "pubDate")
            pub_date = parse_rss_date(pub_date_str) or datetime.now(timezone.utc)

            entries.append({
                "title": title,
                "summary": summary[:500],
                "url": link,
                "date": pub_date,
                "source": source_name,
            })
    else:
        # Atom
        ns["atom"] = "http://www.w3.org/2005/Atom"
        items = root.findall(".//atom:entry", ns)
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items[:max_items]:
            title = _get_xml_text(item, "title") or _get_xml_text(item,
                "{http://www.w3.org/2005/Atom}title")
            summary = (_get_xml_text(item, "summary") or
                       _get_xml_text(item, "content") or
                       _get_xml_text(item, "{http://www.w3.org/2005/Atom}summary") or "")
            summary = re.sub(r"<[^>]+>", " ", summary).strip()
            summary = re.sub(r"\s+", " ", summary)[:500]

            link_elem = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
            link = link_elem.get("href", "") if link_elem is not None else ""
            if not link:
                link = _get_xml_text(item, "id") or _get_xml_text(item,
                    "{http://www.w3.org/2005/Atom}id")

            pub_date_str = (_get_xml_text(item, "published") or
                            _get_xml_text(item, "updated") or
                            _get_xml_text(item, "{http://www.w3.org/2005/Atom}published") or "")
            pub_date = parse_rss_date(pub_date_str) or datetime.now(timezone.utc)

            entries.append({
                "title": title,
                "summary": summary[:500],
                "url": link,
                "date": pub_date,
                "source": source_name,
            })

    print(f"[OK] {source_name} (etree): 获取到 {len(entries)} 条")
    return entries


def _get_xml_text(element, tag):
    """安全获取 XML 元素的文本内容"""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


# ============================================================
# 翻译
# ============================================================

def translate_to_chinese(text, max_retries=3):
    """
    使用免费翻译 API 将文本翻译为中文。
    优先使用 Google Translate，fallback 到 MyMemory。
    """
    if not text or text == "No description available":
        return "暂无描述"

    text = text.strip()
    if len(text) < 5:
        return text

    # 方案1：Google Translate 免费接口
    for attempt in range(max_retries):
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "en",
                "tl": "zh-CN",
                "dt": "t",
                "q": text[:500]
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            translated = ""
            for item in result[0]:
                if item and item[0]:
                    translated += item[0]
            if translated and translated != text:
                return sanitize_text(translated)
        except Exception as e:
            print(f"翻译失败 (Google, 尝试 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)

    # 方案2：MyMemory Translation API
    for attempt in range(max_retries):
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text[:500],
                "langpair": "en|zh-CN"
            }
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("responseStatus") == 200:
                translated = data.get("responseData", {}).get("translatedText", "")
                if translated and translated != text:
                    return sanitize_text(translated)
        except Exception as e:
            print(f"翻译失败 (MyMemory, 尝试 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(1)

    return sanitize_text(text)


# ============================================================
# 锐评生成
# ============================================================

def generate_comment_with_ai(title, description):
    """
    使用 AI 生成针对性犀利锐评。
    尝试 DeepSeek API，失败时使用智能模板。
    """
    prompt = (
        "请给以下AI资讯写一句犀利但不冒犯的中文锐评，1-2句话，"
        "直白说明它的实际作用、解决什么痛点、亮点或局限：\n"
        f"标题：{title}\n描述：{description}\n只输出锐评本身，不要多余解释。"
    )

    # 方案1：DeepSeek API
    try:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        resp = requests.post(url, json=data, headers=headers, timeout=15)
        if resp.status_code == 200:
            result = resp.json()
            comment = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            if comment and len(comment) > 5:
                return sanitize_text(comment.strip())
    except Exception as e:
        print(f"DeepSeek API 调用失败: {e}")

    # 方案2：智能模板
    return sanitize_text(generate_smart_comment(title, description))


def generate_smart_comment(title, description):
    """
    智能模板生成锐评 — 基于内容关键词分析。
    确保每条评论针对特定资讯。
    """
    title_lower = title.lower()
    desc_lower = description.lower()
    combined = f"{title_lower} {desc_lower}"

    is_open_source = any(kw in combined for kw in [
        "open source", "opensource", "open-source", "free", "mit", "apache"])
    is_commercial = any(kw in combined for kw in [
        "api", "pricing", "cost", "subscription", "paid", "launch", "release"])
    is_benchmark = any(kw in combined for kw in [
        "benchmark", "score", "performance", "faster", "improve", "record"])
    is_model_release = any(kw in combined for kw in [
        "llama", "gpt", "claude", "gemini", "model", "release", "launch"])
    is_research = any(kw in combined for kw in [
        "arxiv", "paper", "research", "study", "university", "science"])
    is_regulation = any(kw in combined for kw in [
        "regulation", "policy", "law", "act", "ban", "govern", "eu", "congress"])

    if is_model_release:
        if is_open_source:
            comments = [
                "开源大模型又添新成员，这次能否撼动闭源模型的地位？",
                "开源阵营再下一城，光看参数没用，能跑起来、好不好用才是关键。",
                "社区狂欢，实际部署成本你考虑过吗？"
            ]
        elif is_commercial:
            comments = [
                "新模型发布，效果先观望，按 token 计费的玩法，用得起吗？",
                "又是一个「史上最强」，基准测试刷得飞起，实际应用场景待检验。",
                "商业模型再升级，功能看着牛，钱包要捂紧。"
            ]
        else:
            comments = [
                "新模型来了，是骡子是马拉出来遛遛，别光看宣传看实测。",
                "AI 模型迭代快得飞起，有几个真正解决了实际问题？等落地案例。",
                "模型发布热闹非凡，能不能用、好不好用，用户说了算。"
            ]
    elif is_regulation:
        comments = [
            "监管落地对行业是双刃剑，合规成本飙升，小玩家可能被挤出市场。",
            "政策收紧，大厂合规团队又要扩编了，创新空间还剩多少？",
            "法规来了，短期阵痛难免，长期看是行业走向成熟的必经之路。"
        ]
    elif is_research:
        comments = [
            "论文看着高大上，代码开源了吗？复现了吗？别光说不练。",
            "学术研究值不值，看实验设计和数据集，光看摘要都是纸上谈兵。",
            "新论文发布，先别急着引用，等社区复现和讨论再说。"
        ]
    elif is_benchmark:
        comments = [
            "基准测试成绩亮眼，但测试集和实际场景是两码事，别被数字忽悠。",
            "性能提升显著，能耗和成本呢？多维度权衡才是真实世界。",
            "跑分赢了，实际用起来怎么样？用户体感比数字更重要。"
        ]
    elif is_commercial:
        comments = [
            "商业化产品发布，先看定价策略，再决定要不要入坑。",
            "API 上线了，功能强大但按量付费，小团队用前要算好账。",
            "企业级解决方案，听着高大上，适不适合你的需求另说。"
        ]
    elif is_open_source:
        comments = [
            "开源项目值得支持，文档和社区活跃度比 star 数更重要。",
            "开源是好事，能不能用起来、改起来，才是衡量价值的标准。",
            "GitHub 上的新玩具，先 fork 再说，说不定哪天就成神器了。"
        ]
    else:
        comments = [
            "AI 领域新动态，保持关注，别被营销号带节奏。",
            "行业变化快，今天的热点明天可能就凉了，理性看待。",
            "新趋势值得注意，别盲目跟风，适合自己的才是最好的。"
        ]

    idx = abs(hash(title + description)) % len(comments)
    return comments[idx]


# ============================================================
# 技术动态 — GitHub Trending (已有机能)
# ============================================================

def fetch_tech_news():
    """获取 GitHub Trending AI 项目"""
    try:
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "topic:ai topic:machine-learning",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        headers = {"Accept": "application/vnd.github.v3+json"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("items", [])[:2]:
            title = item["name"]
            summary = item["description"] or "No description available"

            title_cn = translate_to_chinese(title)
            summary_cn = translate_to_chinese(summary)
            comment = generate_comment_with_ai(title, summary)

            results.append({
                "title": title,
                "title_cn": title_cn,
                "summary": summary,
                "summary_cn": summary_cn,
                "comment": comment,
                "url": item["html_url"],
                "date": datetime.now().strftime("%Y-%m-%d")
            })
            time.sleep(2)

        return results
    except Exception as e:
        print(f"GitHub Trending 抓取失败: {e}")
        return []


# ============================================================
# AI论文 — arXiv
# ============================================================

def fetch_arxiv_papers():
    """获取 arXiv 最新 AI 论文"""
    try:
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": "cat:cs.AI",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 5
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results = []

        for entry in root.findall("atom:entry", ns)[:3]:
            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")[:300]
            link = entry.find("atom:id", ns).text

            title_cn = translate_to_chinese(title)
            summary_cn = translate_to_chinese(summary)
            comment = generate_comment_with_ai(title, summary)

            results.append({
                "title": title,
                "title_cn": title_cn,
                "summary": summary + "...",
                "summary_cn": summary_cn + "...",
                "comment": comment,
                "url": link,
                "date": datetime.now().strftime("%Y-%m-%d")
            })
            time.sleep(2)

        return results
    except Exception as e:
        print(f"arXiv 论文抓取失败: {e}")
        return []


# ============================================================
# 新产品 — RSS 动态抓取（替代硬编码模板）
# ============================================================

def fetch_product_news():
    """
    从 TechCrunch / The Verge RSS 抓取 AI 相关新产品/模型资讯。
    取最近 7 天内、AI 相关的 5 条（去重后）。
    全部数据源失败时才使用模板兜底。
    """
    all_entries = []

    for source in RSS_SOURCES_PRODUCT:
        print(f"[INFO] 抓取产品资讯: {source['name']} ({source['url']})")
        entries = fetch_rss_feed(source["name"], source["url"], max_items=30)
        if entries:
            # 筛选 AI 相关
            ai_entries = [e for e in entries if is_ai_related(e["title"], e["summary"])]
            print(f"  -> AI 相关: {len(ai_entries)}/{len(entries)}")
            all_entries.extend(ai_entries)
        time.sleep(1)

    if not all_entries:
        print("[WARN] 所有产品 RSS 源抓取失败，使用模板兜底")
        return _get_product_templates_fallback()

    # 过滤最近 7 天
    all_entries = filter_last_7_days(all_entries)
    print(f"[INFO] 7天内产品资讯: {len(all_entries)} 条")

    if not all_entries:
        print("[WARN] 没有最近 7 天内的产品资讯，使用模板兜底")
        return _get_product_templates_fallback()

    # 去重
    all_entries = deduplicate_entries(all_entries, threshold=0.75)
    print(f"[INFO] 去重后产品资讯: {len(all_entries)} 条")

    # 只取前 5 条
    selected = all_entries[:5]

    results = []
    for entry in selected:
        title = entry["title"]
        summary = entry["summary"]

        title_cn = translate_to_chinese(title)
        summary_cn = translate_to_chinese(summary)
        comment = generate_comment_with_ai(title, summary)

        pub_date = entry.get("date")
        if isinstance(pub_date, datetime):
            date_str = pub_date.strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        results.append({
            "title": title,
            "title_cn": title_cn,
            "summary": summary,
            "summary_cn": summary_cn,
            "comment": comment,
            "url": entry["url"],
            "source": entry.get("source", ""),
            "date": date_str
        })
        time.sleep(2)

    return results


def _get_product_templates_fallback():
    """产品资讯模板兜底（所有 RSS 源失败时使用）"""
    today = datetime.now().strftime("%Y-%m-%d")
    templates = [
        {
            "title": "Claude 3.5 Sonnet - Anthropic's Latest Model",
            "summary": "Anthropic releases Claude 3.5 Sonnet with improved reasoning and coding capabilities.",
            "url": "https://www.anthropic.com/news/claude-3-5-sonnet"
        },
        {
            "title": "GPT-4o Mini - OpenAI's Cost-Effective Model",
            "summary": "OpenAI launches GPT-4o Mini, offering high performance at lower cost.",
            "url": "https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/"
        },
        {
            "title": "Gemini 1.5 Flash - Google's Fast Model",
            "summary": "Google releases Gemini 1.5 Flash for faster inference and lower cost.",
            "url": "https://deepmind.google/technologies/gemini/flash/"
        }
    ]

    results = []
    for t in templates:
        title_cn = translate_to_chinese(t["title"])
        summary_cn = translate_to_chinese(t["summary"])
        comment = generate_comment_with_ai(t["title"], t["summary"])

        results.append({
            "title": t["title"],
            "title_cn": title_cn,
            "summary": t["summary"],
            "summary_cn": summary_cn,
            "comment": comment,
            "url": t["url"],
            "source": "template",
            "date": today
        })
        time.sleep(2)
    return results


# ============================================================
# 行业热点 — RSS 动态抓取（替代硬编码模板）
# ============================================================

def fetch_hotspot_news():
    """
    从 Hacker News (hnrss.org) 抓取 AI 相关行业热点。
    取最近 7 天内、AI 相关的 2 条（去重后）。
    全部失败时使用模板兜底。
    """
    all_entries = []

    for source in RSS_SOURCES_HOTSPOT:
        print(f"[INFO] 抓取行业热点: {source['name']} ({source['url']})")
        entries = fetch_rss_feed(source["name"], source["url"], max_items=30)
        if entries:
            ai_entries = [e for e in entries if is_ai_related(e["title"], e["summary"])]
            print(f"  -> AI 相关: {len(ai_entries)}/{len(entries)}")
            all_entries.extend(ai_entries)
        time.sleep(1)

    if not all_entries:
        print("[WARN] 所有热点 RSS 源抓取失败，使用模板兜底")
        return _get_hotspot_templates_fallback()

    # 过滤最近 7 天
    all_entries = filter_last_7_days(all_entries)
    print(f"[INFO] 7天内热点资讯: {len(all_entries)} 条")

    if not all_entries:
        print("[WARN] 没有最近 7 天内的热点资讯，使用模板兜底")
        return _get_hotspot_templates_fallback()

    # 去重
    all_entries = deduplicate_entries(all_entries, threshold=0.75)
    print(f"[INFO] 去重后热点资讯: {len(all_entries)} 条")

    # 取前 2 条
    selected = all_entries[:2]

    results = []
    for entry in selected:
        title = entry["title"]
        summary = entry["summary"]

        title_cn = translate_to_chinese(title)
        summary_cn = translate_to_chinese(summary)
        comment = generate_comment_with_ai(title, summary)

        pub_date = entry.get("date")
        if isinstance(pub_date, datetime):
            date_str = pub_date.strftime("%Y-%m-%d")
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        results.append({
            "title": title,
            "title_cn": title_cn,
            "summary": summary,
            "summary_cn": summary_cn,
            "comment": comment,
            "url": entry["url"],
            "source": entry.get("source", ""),
            "date": date_str
        })
        time.sleep(2)

    return results


def _get_hotspot_templates_fallback():
    """行业热点模板兜底（所有 RSS 源失败时使用）"""
    today = datetime.now().strftime("%Y-%m-%d")
    templates = [
        {
            "title": "AI Regulation Updates - EU AI Act Implementation",
            "summary": "European Union implements AI Act, setting global standard for AI regulation.",
            "url": "https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai"
        },
        {
            "title": "AI Chip Market Competition Intensifies",
            "summary": "NVIDIA, AMD, and Intel compete fiercely in AI chip market with new product launches.",
            "url": "https://www.reuters.com/technology/artificial-intelligence/"
        }
    ]

    results = []
    for t in templates:
        title_cn = translate_to_chinese(t["title"])
        summary_cn = translate_to_chinese(t["summary"])
        comment = generate_comment_with_ai(t["title"], t["summary"])

        results.append({
            "title": t["title"],
            "title_cn": title_cn,
            "summary": t["summary"],
            "summary_cn": summary_cn,
            "comment": comment,
            "url": t["url"],
            "source": "template",
            "date": today
        })
        time.sleep(2)
    return results


# ============================================================
# 报告生成 & 保存
# ============================================================

def generate_daily_report():
    """生成每日报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    report = {"date": today, "items": []}

    # 技术动态 (2条) — GitHub Trending
    print("\n=== 1/4 技术动态 (GitHub Trending) ===")
    tech_items = fetch_tech_news()
    for item in tech_items[:2]:
        report["items"].append({"category": "技术动态", **item})

    # AI论文 (3条) — arXiv
    print("\n=== 2/4 AI论文 (arXiv) ===")
    paper_items = fetch_arxiv_papers()
    for item in paper_items[:3]:
        report["items"].append({"category": "AI论文", **item})

    # 新产品 (3条) — RSS 动态抓取
    print("\n=== 3/4 新产品 (RSS) ===")
    product_items = fetch_product_news()
    for item in product_items[:3]:
        report["items"].append({"category": "新产品", **item})

    # 行业热点 (2条) — RSS 动态抓取
    print("\n=== 4/4 行业热点 (RSS) ===")
    hotspot_items = fetch_hotspot_news()
    for item in hotspot_items[:2]:
        report["items"].append({"category": "行业热点", **item})

    print(f"\n=== 报告生成完毕: 共 {len(report['items'])} 条 ===")
    return report


def save_report(report):
    """保存报告到 JSON 文件"""
    date_str = report["date"]
    filename = f"{date_str}.json"

    # 保存到 data 目录
    data_path = DATA_DIR / filename
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 复制到 docs/data 目录（GitHub Pages）
    docs_path = DOCS_DATA_DIR / filename
    with open(docs_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 更新 latest.json
    latest_path = DOCS_DATA_DIR / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 更新索引
    update_index(date_str)

    print(f"报告已保存: {data_path}")
    return data_path


def update_index(current_date):
    """更新报告索引"""
    index_path = DOCS_DATA_DIR / "index.json"

    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"dates": []}

    if current_date not in index["dates"]:
        index["dates"].insert(0, current_date)
        index["dates"].sort(reverse=True)

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"索引已更新: {index_path}")


# ============================================================
# 入口
# ============================================================

def main():
    """主函数"""
    print("=" * 60)
    print("  每日AI资讯日报 — 爬虫 v2.0")
    print(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  feedparser: {'已安装' if HAS_FEEDPARSER else '未安装 (fallback xml.etree)'}")
    print("=" * 60)

    report = generate_daily_report()
    save_report(report)
    print("\n✅ 报告生成完成！")


if __name__ == "__main__":
    main()
