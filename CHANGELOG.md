# 修改日志

## 2026-07-02 — 修复 Pages 部署 & 优化 GitHub Trending 抓取

### 🐛 修复

#### 1. GitHub Pages 部署失败

**问题**：`docs/` 目录下缺少 `.nojekyll` 文件，GitHub Pages 尝试用 Jekyll 构建纯静态 HTML 站点，导致部署流程失败（`state: failure`）。网站停留在旧版本无法更新。

**修复**：
- 在 `docs/` 目录添加 `.nojekyll` 空文件，告知 GitHub Pages 跳过 Jekyll 处理
- 首次修复后 Pages 构建在 10 秒内成功，网站恢复正常上线

**影响文件**：`docs/.nojekyll`（新建）

### 🔧 优化

#### 2. `fetch_tech_news()` — GitHub API 查询改为按"最近创建时间"过滤

**问题**：旧查询参数 `q: "topic:ai topic:machine-learning"` + `sort: stars` 返回的是 AI 领域**历史累计 Star 最高**的仓库（如 TensorFlow、PyTorch），每次运行结果几乎不变，违背"技术动态"的时效性要求。

**修复**：改用动态日期过滤，只查询最近 7 天内新建的仓库：

| 项目 | 旧 | 新 |
|------|-----|-----|
| 查询 | `topic:ai topic:machine-learning` | `topic:ai topic:machine-learning created:>2026-06-25`（动态） |
| 日期 | 无 | `datetime.now() - timedelta(days=7)` 运行时动态计算 |
| 认证 | 无 Authorization | 读取 `GITHUB_TOKEN` 环境变量，有则带 token（60→5000次/小时） |
| 日志 | 无 | 打印认证状态 + 日期过滤条件 |

**实现要点**：
- 日期使用 `datetime.now()` 动态生成，不写死
- `os.getenv("GITHUB_TOKEN")` 读取环境变量，加 try-except 降级处理
- 异常时返回空列表，不中断工作流
- 函数签名与返回值结构完全不变，调用方无感知

**影响文件**：`scripts/crawler.py`（第 570-627 行，含顶部新增 `import os`）

### ✨ 新增

#### 3. 环境变量配置支持

**问题**：之前所有 API 请求均为未认证状态，GitHub API 限额仅 60 次/小时，反复调试抓取逻辑时容易触发限流。

**修复**：
- 新建 `.env.example`，提供 `GITHUB_TOKEN` 配置模板和获取说明
- `.gitignore` 新增 `.env` 排除规则，防止 token 泄露
- 代码中通过 `os.getenv("GITHUB_TOKEN")` 读取，未配置时自动降级

**影响文件**：
- `.env.example`（新建）
- `.gitignore`（新增 `.env` 规则）

**使用方式**：
```bash
cp .env.example .env
# 编辑 .env，填入: GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

### 📦 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `docs/.nojekyll` | 新建 | 修复 Pages 部署 |
| `scripts/crawler.py` | 修改 | `fetch_tech_news()` 重构 + `import os` |
| `.env.example` | 新建 | GITHUB_TOKEN 配置模板 |
| `.gitignore` | 修改 | 新增 `.env` 排除规则 |

---

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
