// 配置
const DATA_BASE_URL = 'data';
const INDEX_FILE = `${DATA_BASE_URL}/index.json`;
const LATEST_FILE = `${DATA_BASE_URL}/latest.json`;

// 分类颜色映射
const CATEGORY_COLORS = {
    '技术动态': 'tech',
    'AI论文': 'paper',
    '新产品': 'product',
    '行业热点': 'hot'
};

// 格式化日期显示
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()];
    return `${year}年${month}月${day}日 ${weekday}`;
}

// 加载首页数据
async function loadHomePage() {
    const container = document.getElementById('news-container');
    const dateTitle = document.getElementById('date-title');

    try {
        // 加载最新数据
        const response = await fetch(LATEST_FILE);
        if (!response.ok) {
            throw new Error('无法加载数据');
        }

        const data = await response.json();

        // 更新标题
        dateTitle.textContent = formatDate(data.date);

        // 清空容器
        container.innerHTML = '';

        // 渲染新闻卡片
        data.items.forEach((item, index) => {
            const card = createNewsCard(item, index + 1);
            container.appendChild(card);
        });

    } catch (error) {
        console.error('加载失败:', error);
        container.innerHTML = `
            <div class="loading">
                <p>数据加载失败，请稍后重试</p>
                <p style="font-size: 0.9rem; margin-top: 8px;">错误信息: ${error.message}</p>
            </div>
        `;
    }
}

// 创建新闻卡片（更新版 - 支持中文和锐评）
function createNewsCard(item, index) {
    const card = document.createElement('div');
    card.className = 'news-card';

    const categoryClass = CATEGORY_COLORS[item.category] || 'tech';

    // 使用中文标题（如果有），否则使用英文
    const displayTitle = item.title_cn || item.title;
    const displaySummary = item.summary_cn || item.summary || '';
    const hasSummary = displaySummary && displaySummary.length > 0;

    card.innerHTML = `
        <div class="news-card-header">
            <span class="tag ${categoryClass}">${item.category}</span>
            <span class="news-index">#${index}</span>
        </div>
        <h3 class="news-card-title">
            <a href="${item.url}" target="_blank" rel="noopener">${displayTitle}</a>
        </h3>
        ${item.title_cn && item.title ? `<p class="news-card-title-en" style="font-size:0.85rem;color:#999;margin-bottom:8px;">${item.title}</p>` : ''}
        ${hasSummary ? `
        <div class="news-card-summary-cn">${displaySummary}</div>
        ` : ''}
        ${item.comment ? `
        <div class="comment-section">
            <div class="comment-label">犀利锐评</div>
            <div class="comment-text">${item.comment}</div>
        </div>
        ` : ''}
        <div class="news-card-footer">
            <a href="${item.url}" class="news-card-link" target="_blank" rel="noopener">阅读原文 →</a>
            <span class="news-card-date">${item.date || ''}</span>
        </div>
    `;

    return card;
}

// 加载历史列表
async function loadHistoryPage() {
    const container = document.getElementById('history-list');

    try {
        const response = await fetch(INDEX_FILE);
        if (!response.ok) {
            throw new Error('无法加载历史记录');
        }

        const data = await response.json();

        if (!data.dates || data.dates.length === 0) {
            container.innerHTML = '<div class="loading">暂无历史记录</div>';
            return;
        }

        // 清空容器
        container.innerHTML = '';

        // 渲染历史条目
        data.dates.forEach(date => {
            const item = createHistoryItem(date);
            container.appendChild(item);
        });

    } catch (error) {
        console.error('加载失败:', error);
        container.innerHTML = `
            <div class="loading">
                <p>历史记录加载失败</p>
                <p style="font-size: 0.9rem; margin-top: 8px;">错误信息: ${error.message}</p>
            </div>
        `;
    }
}

// 创建历史条目
function createHistoryItem(date) {
    const item = document.createElement('div');
    item.className = 'history-item';

    item.innerHTML = `
        <span class="history-date">${formatDate(date)}</span>
        <a href="index.html?date=${date}" class="history-link">查看详情 →</a>
    `;

    return item;
}

// 根据URL参数加载特定日期的数据
async function loadSpecificDate() {
    const urlParams = new URLSearchParams(window.location.search);
    const date = urlParams.get('date');

    if (!date) {
        return false;
    }

    const container = document.getElementById('news-container');
    const dateTitle = document.getElementById('date-title');

    try {
        const response = await fetch(`${DATA_BASE_URL}/${date}.json`);
        if (!response.ok) {
            throw new Error('无法加载该日期的数据');
        }

        const data = await response.json();

        dateTitle.textContent = formatDate(data.date);
        container.innerHTML = '';

        data.items.forEach((item, index) => {
            const card = createNewsCard(item, index + 1);
            container.appendChild(card);
        });

        return true;

    } catch (error) {
        console.error('加载失败:', error);
        container.innerHTML = '<div class="loading">该日期的数据不存在</div>';
        return true;
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', async () => {
    const isHistoryPage = window.location.pathname.includes('history.html');
    const isAboutPage = window.location.pathname.includes('about.html');

    if (isAboutPage) {
        // 关于页面无需加载数据
        return;
    }

    if (isHistoryPage) {
        await loadHistoryPage();
    } else {
        // 检查是否有特定日期参数
        const hasSpecificDate = await loadSpecificDate();

        if (!hasSpecificDate) {
            await loadHomePage();
        }
    }
});

// 自动刷新（每小时检查一次新数据）
setInterval(async () => {
    if (!window.location.pathname.includes('index.html') &&
        !window.location.pathname.endsWith('/') &&
        !window.location.pathname.endsWith('index.html')) {
        return;
    }

    try {
        const response = await fetch(LATEST_FILE + '?t=' + Date.now());
        if (response.ok) {
            const data = await response.json();
            const dateTitle = document.getElementById('date-title');
            if (dateTitle) {
                const currentDate = dateTitle.textContent;
                const newDate = formatDate(data.date);
                if (currentDate !== newDate) {
                    // 有新数据，刷新页面
                    window.location.reload();
                }
            }
        }
    } catch (error) {
        console.error('检查更新失败:', error);
    }
}, 3600000); // 1小时
