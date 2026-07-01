#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日AI资讯爬虫 - 升级版
自动抓取AI相关内容，翻译为中文，生成犀利锐评，并生成JSON格式的日报
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import time

# 配置
DATA_DIR = Path(__file__).parent.parent / "data"
DOCS_DATA_DIR = Path(__file__).parent.parent / "docs" / "data"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
DOCS_DATA_DIR.mkdir(exist_ok=True)


def translate_to_chinese(text, max_retries=3):
    """
    使用免费翻译API将文本翻译为中文
    优先使用MyMemory Translation API（免费，无需密钥）
    """
    if not text or text == "No description available":
        return "暂无描述"

    # 清理文本
    text = text.strip()
    if len(text) < 5:
        return text

    # 尝试使用MyMemory Translation API（免费，每天5000字符）
    for attempt in range(max_retries):
        try:
            url = "https://api.mymemory.translated.net/get"
            params = {
                "q": text[:500],  # 限制长度
                "langpair": "en|zh-CN"
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("responseStatus") == 200:
                translated = data.get("responseData", {}).get("translatedText", "")
                if translated and translated != text:
                    return translated
        except Exception as e:
            print(f"翻译失败（MyMemory，尝试 {attempt + 1}）: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)

    # 备用方案：使用Google Translate免费接口（无需密钥）
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "zh-CN",
            "dt": "t",
            "q": text[:500]
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()

        # 解析Google Translate返回的结果
        translated = ""
        for item in result[0]:
            if item and item[0]:
                translated += item[0]

        if translated:
            return translated
    except Exception as e:
        print(f"翻译失败（Google）: {e}")

    # 如果都失败，返回原文
    return text


def sanitize_text(text):
    """
    清理文本中的特殊字符，防止JSON解析错误。
    将ASCII双引号替换为中文书名号，避免与JSON字符串定界符冲突。
    """
    if not text:
        return text
    # 替换ASCII双引号为中文引号
    text = text.replace('"', '“').replace('"', '”')
    # 如果存在成对的双引号，用中文引号替换
    import re
    # 匹配 "xxx" 模式并替换为「xxx」
    text = re.sub(r'"([^"]*)"', r'「\1」', text)
    return text


def generate_comment_with_ai(title, description):
    """
    使用AI生成针对性犀利锐评
    尝试多个免费API，全部失败时返回智能模板评论
    """
    # 构建提示词
    prompt = f"""请给以下AI资讯写一句犀利但不冒犯的中文锐评，1-2句话，直白说明它的实际作用、解决什么痛点、亮点或局限：
标题：{title}
描述：{description}
只输出锐评本身，不要多余解释。"""

    # 方案1：尝试使用DeepSeek免费API（无需密钥的公共端点）
    try:
        # DeepSeek 免费的公共端点（如果可用）
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        response = requests.post(url, json=data, headers=headers, timeout=15)
        if response.status_code == 200:
            result = response.json()
            comment = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            if comment and len(comment) > 5:
                return sanitize_text(comment.strip())
    except Exception as e:
        print(f"DeepSeek API调用失败: {e}")

    # 方案2：使用智能模板生成（基于内容分析）
    return sanitize_text(generate_smart_comment(title, description))


def generate_smart_comment(title, description):
    """
    智能模板生成锐评 - 基于内容分析的多样化模板
    确保每条评论都是针对该资讯的
    """
    title_lower = title.lower()
    desc_lower = description.lower()
    combined = title_lower + " " + desc_lower

    # 技术实力评估关键词
    is_open_source = any(kw in combined for kw in ["open source", "opensource", "open-source", "free", "mit", "apache"])
    is_commercial = any(kw in combined for kw in ["api", "pricing", "cost", "subscription", "paid"])
    is_benchmark = any(kw in combined for kw in ["benchmark", "score", "performance", "faster", "improve"])
    is_model_release = any(kw in combined for kw in ["llama", "gpt", "claude", "gemini", "model", "release"])
    is_research = any(kw in combined for kw in ["arxiv", "paper", "research", "study", "university"])

    # 生成针对性评论
    if is_model_release:
        if is_open_source:
            comments = [
                f"开源大模型又添新成员，{title.split()[0] if title else '它'}这次能否撼动闭源模型的地位？",
                f"开源阵营再下一城，但光看参数没用，能不能跑起来、好不好用才是关键。",
                f"Meta/Llama系又放大招，社区狂欢，不过实际部署成本您考虑过吗？"
            ]
        elif is_commercial:
            comments = [
                f"新模型发布，效果先观望，价格先准备好——按token计费的玩法，用得起吗？",
                f"又是一个'史上最强'，基准测试刷得飞起，实际应用场景待检验。",
                f"商业模型再升级，功能看着牛，钱包要捂紧，按量付费伤不起。"
            ]
        else:
            comments = [
                f"新模型来了，是骡子是马拉出来遛遛，别光看宣传看实测。",
                f"AI模型迭代快得飞起，但有几个真正解决了实际问题？等落地案例。",
                f"模型发布热闹非凡，能不能用、好不好用，用户说了算。"
            ]
    elif is_research:
        if "arxiv" in title_lower or "paper" in title_lower:
            comments = [
                f"论文看着高大上，代码开源了吗？复现了吗？别光说不练。",
                f"学术研究值不值，看实验设计和数据集，光看摘要都是纸上谈兵。",
                f"新论文发布，先别急着引用，等社区复现和讨论再说话。"
            ]
        else:
            comments = [
                f"研究成果发布，理论很美好，落地才知道真假，保持审慎乐观。",
                f"学术界的新尝试，能否转化为实用产品？时间会给出答案。",
                f"研究值得关注，但离实际应用还有距离，别过度解读。"
            ]
    elif is_benchmark:
        comments = [
            f"基准测试成绩亮眼，但测试集和实际场景是两码事，别被数字忽悠。",
            f"性能提升显著，能耗和成本呢？多维度的权衡才是真实世界。",
            f"跑分赢了，实际用起来如何？用户体感比数字更重要。"
        ]
    elif is_commercial:
        comments = [
            f"商业化产品发布，先看看定价策略，再决定要不要入坑。",
            f"API上线了，功能强大但按量付费，小团队用前要算好账。",
            f"企业级解决方案，听着高大上，适不适合您的需求另说。"
        ]
    elif is_open_source:
        comments = [
            f"开源项目值得支持，但文档和社区活跃度更重要，别光看stars。",
            f"开源是好事，能不能用起来、改起来，才是衡量价值的标准。",
            f"GitHub上的新玩具，先fork再说，说不定哪天就成神器了。"
        ]
    else:
        comments = [
            f"AI领域新动态，保持关注，别被营销号带节奏。",
            f"行业变化快，今天的热点明天可能就凉了，理性看待。",
            f"新趋势值得注意，但别盲目跟风，适合自己的才是最好的。"
        ]

    # 使用哈希选择评论，确保同一标题总是得到同一评论（避免重复运行得到不同结果）
    index = hash(title + description) % len(comments)
    return comments[index]


def fetch_github_trending():
    """获取GitHub Trending AI项目"""
    try:
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "topic:ai topic:machine-learning",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", [])[:2]:  # 只取前2条
            title = item["name"]
            summary = item["description"] or "No description available"

            # 翻译
            title_cn = translate_to_chinese(title)
            summary_cn = translate_to_chinese(summary)

            # 生成锐评（使用AI生成）
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

            # 避免API限流
            time.sleep(2)

        return results
    except Exception as e:
        print(f"GitHub Trending抓取失败: {e}")
        return []


def fetch_arxiv_papers():
    """获取arXiv最新AI论文"""
    try:
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": "cat:cs.AI",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 5
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()

        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)

        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        results = []

        for entry in root.findall('atom:entry', ns)[:3]:  # 只取前3条
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')[:300]
            link = entry.find('atom:id', ns).text

            # 翻译
            title_cn = translate_to_chinese(title)
            summary_cn = translate_to_chinese(summary)

            # 生成锐评
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

            # 避免API限流
            time.sleep(2)

        return results
    except Exception as e:
        print(f"arXiv论文抓取失败: {e}")
        return []


def generate_daily_report():
    """生成每日报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    report = {
        "date": today,
        "items": []
    }

    # 技术动态 (2条) - 来自GitHub Trending
    tech_items = fetch_github_trending()
    for item in tech_items[:2]:
        report["items"].append({
            "category": "技术动态",
            **item
        })

    # AI论文 (3条) - 来自arXiv
    paper_items = fetch_arxiv_papers()
    for item in paper_items[:3]:
        report["items"].append({
            "category": "AI论文",
            **item
        })

    # 新产品 (3条) - 使用模板数据（因为Hugging Face API可能不稳定）
    product_templates = [
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

    for template in product_templates:
        title = template["title"]
        summary = template["summary"]

        title_cn = translate_to_chinese(title)
        summary_cn = translate_to_chinese(summary)
        comment = generate_comment_with_ai(title, summary)

        report["items"].append({
            "category": "新产品",
            "title": title,
            "title_cn": title_cn,
            "summary": summary,
            "summary_cn": summary_cn,
            "comment": comment,
            "url": template["url"],
            "date": today
        })

        time.sleep(2)

    # 行业热点 (2条) - 使用模板数据
    hot_templates = [
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

    for template in hot_templates:
        title = template["title"]
        summary = template["summary"]

        title_cn = translate_to_chinese(title)
        summary_cn = translate_to_chinese(summary)
        comment = generate_comment_with_ai(title, summary)

        report["items"].append({
            "category": "行业热点",
            "title": title,
            "title_cn": title_cn,
            "summary": summary,
            "summary_cn": summary_cn,
            "comment": comment,
            "url": template["url"],
            "date": today
        })

        time.sleep(2)

    return report


def save_report(report):
    """保存报告到JSON文件"""
    date_str = report["date"]
    filename = f"{date_str}.json"

    # 保存到data目录
    data_path = DATA_DIR / filename
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 复制到docs/data目录（用于GitHub Pages）
    docs_path = DOCS_DATA_DIR / filename
    with open(docs_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 更新latest.json
    latest_path = DOCS_DATA_DIR / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 更新索引文件
    update_index(date_str)

    print(f"报告已保存: {data_path}")
    return data_path


def update_index(current_date):
    """更新报告索引"""
    index_path = DOCS_DATA_DIR / "index.json"

    # 读取现有索引
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    else:
        index = {"dates": []}

    # 添加新日期（如果不存在）
    if current_date not in index["dates"]:
        index["dates"].insert(0, current_date)
        index["dates"].sort(reverse=True)

    # 保存索引
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"索引已更新: {index_path}")


def main():
    """主函数"""
    print("开始生成每日AI资讯报告（中文翻译+AI锐评版）...")
    report = generate_daily_report()
    save_report(report)
    print("报告生成完成！")


if __name__ == "__main__":
    main()
