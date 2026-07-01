# 修改日志

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
