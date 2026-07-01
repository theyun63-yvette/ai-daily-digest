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

## 🚀 在线访问

**GitHub Pages**: [https://theyun63-yvette.github.io/ai-daily-digest/](https://theyun63-yvette.github.io/ai-daily-digest/)

## 📊 技术栈

- **爬虫**: Python + Requests
- **前端**: 纯 HTML + CSS + JavaScript
- **自动化**: GitHub Actions
- **部署**: GitHub Pages
- **存储**: JSON文件

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

### 3. 运行爬虫

```bash
python scripts/crawler.py
```

### 4. 本地预览

使用任意HTTP服务器预览网站，例如：

```bash
# Python 3
cd docs
python -m http.server 8000

# 或使用Node.js
npx serve docs
```

然后访问 `http://localhost:8000`

## 📁 项目结构

```
ai-daily-digest/
├── .github/
│   └── workflows/
│       └── daily-update.yml    # GitHub Actions配置
├── scripts/
│   └── crawler.py              # 爬虫脚本
├── data/                       # 原始数据（JSON）
├── docs/                       # GitHub Pages网站
│   ├── index.html              # 首页
│   ├── history.html            # 历史日报
│   ├── about.html              # 关于页面
│   ├── css/
│   │   └── style.css          # 样式文件
│   ├── js/
│   │   └── main.js            # 前端逻辑
│   └── data/                  # 网站数据（JSON）
├── requirements.txt             # Python依赖
└── README.md                   # 项目说明
```

## ⚙️ GitHub Actions配置

工作流文件：`.github/workflows/daily-update.yml`

**触发条件**：
- 每天UTC 0点（北京时间早上8点）自动运行
- 支持手动触发
- Push到main/master分支时运行

**工作流程**：
1. 检出代码
2. 设置Python环境
3. 安装依赖
4. 运行爬虫脚本
5. 提交并推送更新
6. GitHub Pages自动部署

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

- [GitHub API](https://docs.github.com/en/rest) - GitHub Trending
- [arXiv API](https://arxiv.org/help/api) - 学术论文
- [Hugging Face API](https://huggingface.co/docs/hub/api) - AI模型

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系

如有问题或建议，请提交GitHub Issue。

---

⭐ 如果这个项目对您有帮助，欢迎Star支持！
