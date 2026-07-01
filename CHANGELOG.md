# 修改日志

## 2026-07-01 (v2.0) — RSS 动态抓取 & 去硬编码

### 🚀 重大更新

#### 1. 新产品 & 行业热点改为动态 RSS 抓取

**问题**：`product_templates` 和 `hot_templates` 是写死的，永远返回 2024 年的旧信息（Claude 3.5 / GPT-4o Mini / Gemini 1.5 Flash），导致网站每天内容完全一样。

**修复**：重写 `fetch_product_news()` 和 `fetch_hotspot_news()`，改为从真实 RSS 源动态抓取：

| 板块 | 数据源 | 数量 |
|------|--------|------|
| 新产品 | TechCrunch RSS + The Verge RSS | 去重后取最新 5 条 |
| 行业热点 | Hacker News (hnrss.org) | 去重后取最新 2 条 |

**新增功能**：
- 🔍 **AI 关键词筛选**：40+ 关键词智能识别 AI 相关内容（LLM/GPT/Claude/Gemini/NVIDIA 等）
- 📅 **7天过滤**：只保留最近 7 天内的资讯
- 🔄 **标题去重**：使用 `SequenceMatcher` 相似度 > 75% 视为重复
- 🛡️ **多层降级**：RSS → fallback 到 xml.etree → 全部失败则用模板兜底
- 📝 **日志输出**：每步都有日志，方便排查抓取链路问题

#### 2. JSON 双引号防护

**问题**：爬虫生成的评论中可能包含 ASCII 双引号，导致 JSON 解析失败。
**修复**：新增 `sanitize_text()` 函数，自动将成对双引号替换为中文书名号「」。

### 📦 新增依赖

| 包 | 版本 | 用途 |
|----|------|------|
| `feedparser` | >= 6.0 | RSS/Atom feed 解析（可选，未安装时自动 fallback 到 xml.etree） |

### 🔧 其他修改

- `.github/workflows/daily-update.yml`：改为 `pip install -r requirements.txt`
- `requirements.txt`：新增 `feedparser>=6.0.0`

---

## 2026-07-01 — 修复占位链接 & 迁移仓库

### 🔧 修复

#### 1. 替换 `example.com` 占位符链接为真实来源

**问题**：爬虫脚本和静态数据中存在 `example.com` 占位链接，导致用户点击"阅读原文"后跳转到无效页面。

**影响范围**：
- `scripts/crawler.py` 第 370 行 — `hot_templates` 中 "AI Chip Market Competition Intensifies" 的 URL
- `data/2024-01-15.json` 第 64、71 行 — "AI芯片市场竞争加剧" 和 "欧盟 AI Act 正式生效"
- `docs/data/2024-01-15.json` 第 64、71 行 — 同上（GitHub Pages 部署副本）

**修复内容**：

| 文件 | 原标题 | 旧 URL | 新 URL |
|------|--------|--------|--------|
| `scripts/crawler.py` | AI Chip Market Competition Intensifies | `https://example.com/ai-chip-market-2026` | `https://www.reuters.com/technology/artificial-intelligence/` |
| `data/2024-01-15.json` | AI 芯片市场竞争加剧 - NVIDIA vs AMD | `https://example.com/ai-chip-market` | `https://www.reuters.com/technology/artificial-intelligence/` |
| `data/2024-01-15.json` | 欧盟 AI Act 正式生效 | `https://example.com/eu-ai-act` | `https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai` |
| `docs/data/2024-01-15.json` | AI 芯片市场竞争加剧 - NVIDIA vs AMD | `https://example.com/ai-chip-market` | `https://www.reuters.com/technology/artificial-intelligence/` |
| `docs/data/2024-01-15.json` | 欧盟 AI Act 正式生效 | `https://example.com/eu-ai-act` | `https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai` |

#### 2. 仓库名称规范化（去除尾部多余字符）

**问题**：原仓库 `succeed-ai-daily-digest.` 名称末尾多了一个点 `.`，导致 URL 显示异常。此外，本地 git remote 指向 `ai-daily-digest.1.git` 而非干净的仓库名。

**修复**：新仓库使用干净名称 `ai-daily-digest`（无 trailing dot）。

### 🔄 迁移

#### 3. GitHub 账号迁移

- **旧账号**：`zhouyvette567-stack`
- **新账号**：`theyun63-yvette`

**涉及文件**：
- `README.md` — GitHub Pages URL 和 clone 地址
- `docs/about.html` — 项目地址链接

### 📝 说明

- `example.com` 占位符问题根因：`crawler.py` 的 `hot_templates` 列表使用硬编码模板数据，而非从 API 动态抓取。建议后续版本改为从新闻 API（如 NewsAPI）实时获取行业热点资讯。
