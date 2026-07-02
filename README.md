# 每日AI资讯日报 🤖

一个极简、干净的AI资讯聚合网站，每天自动抓取并整理10条精选AI内容。

![GitHub Actions Status](https://img.shields.io/badge/更新-每日-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

## ✨ 特性

- 🎯 **精选内容**：每天10条AI资讯，分为4个类别
  - 技术动态 (2条)：GitHub Trending AI项目
  - AI论文 (3条)：arXiv最新研究论文
  - 新产品 (3条)：Hugging Face热门模型
  - 行业热点 (2条)：AI行业重大新闻

- 🤖 **全自动化**：使用GitHub Actions每天自动运行
  - 自动抓取最新内容
  - 自动生成JSON数据
  - 自动更新网站

- 🎨 **极简设计**：
  - 响应式设计，适配手机/平板/电脑
  - 柔和配色，视觉舒适
  - 无广告、无弹窗、无冗余元素

- 📂 **纯静态**：无需数据库，使用JSON文件存储

- 💬 **企业微信推送**：每天自动推送日报到企业微信群机器人
  - 支持 Markdown 格式消息
  - DeepSeek AI 生成犀利锐评
  - 消息长度自适应（<4096字节）

## 🚀 在线访问

**GitHub Pages**: [https://theyun63-yvette.github.io/ai-daily-digest/](https://theyun63-yvette.github.io/ai-daily-digest/)

## 📊 技术栈

- **爬虫**: Python + Requests + Feedparser
- **AI锐评**: DeepSeek API
- **推送**: 企业微信机器人 Webhook
- **前端**: 纯 HTML + CSS + JavaScript
- **自动化**: GitHub Actions（每天北京时间 9:00）
- **部署**: GitHub Pages
- **存储**: JSON文件
- **环境变量**: python-dotenv

## 🛠️ 本地开发

### 1. 克隆项目

```bash
git clone https://github.com/theyun63-yvette/ai-daily-digest.git
cd ai-daily-digest
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入实际值：
#   WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
#   DEEPSEEK_API_KEY=sk-xxx
#   GITHUB_TOKEN=ghp_xxx
```

### 4. 运行爬虫

```bash
python scripts/crawler.py
```

### 5. 本地预览

使用任意HTTP服务器预览网站，例如：

```bash
# Python 3
cd docs
python -m http.server 8000

# 或使用Node.js
npx serve docs
```

然后访问 `http://localhost:8000`

### 6. 测试企业微信推送

确保 `.env` 中配置了 `WECOM_WEBHOOK_URL`，运行爬虫后会自动推送日报到企业微信群。

## 📁 项目结构

```
ai-daily-digest/
├── .github/workflows/
│   └── daily-update.yml          # GitHub Actions（每天9:00自动运行）
├── scripts/
│   ├── crawler.py                # 爬虫主程序
│   └── notifier.py               # 企业微信推送模块
├── data/                         # 原始数据（JSON）
├── docs/                         # GitHub Pages 网站
│   ├── index.html / history.html / about.html
│   ├── css/ / js/ / data/
├── .env.example                  # 环境变量配置模板
├── requirements.txt              # Python 依赖
├── CHANGELOG.md                  # 修改日志
└── README.md                     # 项目说明
```

## ⚙️ GitHub Actions配置

工作流文件：`.github/workflows/daily-update.yml`

**触发条件**：
- 每天 UTC 1:00（北京时间早上 9:00）自动运行
- 支持手动触发（workflow_dispatch）
- Push 到 main/master 分支时运行

**工作流程**：
1. 检出代码
2. 设置 Python 环境
3. 安装依赖
4. 运行爬虫脚本（含 AI 锐评 + 企业微信推送）
5. 提交并推送数据更新
6. GitHub Pages 自动部署

**需要的 Secrets**（在 Settings → Secrets and variables → Actions 中配置）：

| Secret | 说明 | 必需 |
|--------|------|------|
| `WECOM_WEBHOOK_URL` | 企业微信机器人 Webhook 地址 | 推送功能需要 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | AI 锐评需要 |
| `GITHUB_TOKEN` | 自动提供，无需手动配置 | 自动 |

## 📝 数据结构

每日数据保存为JSON格式：

```json
{
  "date": "2024-01-15",
  "items": [
    {
      "category": "技术动态",
      "title": "项目标题",
      "summary": "内容摘要",
      "url": "原文链接",
      "date": "2024-01-15"
    }
  ]
}
```

索引文件 `data/index.json`：

```json
{
  "dates": ["2024-01-15", "2024-01-14", ...]
}
```

## 🎨 设计说明

**色彩规范**：
- 技术动态：`#3498db` (蓝色)
- AI论文：`#9b59b6` (紫色)
- 新产品：`#2ecc71` (绿色)
- 行业热点：`#e67e22` (橙色)

**响应式断点**：
- 桌面：> 768px
- 平板：480px - 768px
- 手机：< 480px

## 📜 开源协议

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 数据来源

- [GitHub API](https://docs.github.com/en/rest) — 技术动态（AI/ML 热门仓库）
- [arXiv API](https://arxiv.org/help/api) — AI 学术论文
- [TechCrunch RSS](https://techcrunch.com/feed/) / [The Verge RSS](https://www.theverge.com/rss/index.xml) — 新产品资讯
- [Hacker News](https://hnrss.org/frontpage) — 行业热点
- [DeepSeek API](https://platform.deepseek.com/) — AI 锐评生成
- [MyMemory API](https://mymemory.translated.net/) / Google Translate — 中英翻译

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系

如有问题或建议，请提交GitHub Issue。

---

⭐ 如果这个项目对您有帮助，欢迎Star支持！
