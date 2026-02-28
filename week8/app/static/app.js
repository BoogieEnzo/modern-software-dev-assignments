// OS Paper Hub - Frontend JavaScript
const API_BASE = '/api';

// State
let currentTab = 'papers';
let papers = [];

// DOM Elements
const papersList = document.getElementById('papers-list');
const searchResults = document.getElementById('search-results');
const favoritesList = document.getElementById('favorites-list');
const modal = document.getElementById('paper-modal');
const paperDetail = document.getElementById('paper-detail');
const searchInput = document.getElementById('search-input');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadPapers();
    loadFavorites();
});

// Tab Navigation
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            switchTab(tabId);
        });
    });
    
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadPapers);
    
    // Local search - filter papers in real-time
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (!query) {
            renderPapers(papers, papersList);
        } else {
            const filtered = papers.filter(p => 
                (p.title && p.title.toLowerCase().includes(query)) ||
                (p.authors && p.authors.toLowerCase().includes(query))
            );
            renderPapers(filtered, papersList);
        }
    });
    
    // ArXiv search
    document.getElementById('arxiv-search-btn').addEventListener('click', () => {
        switchTab('search');
        searchArxiv();
    });
    document.getElementById('arxiv-search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            switchTab('search');
            searchArxiv();
        }
    });
    
    // Modal close
    document.querySelector('.close').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
}

function switchTab(tabId) {
    currentTab = tabId;
    
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${tabId}-tab`).classList.add('active');
}

// API Functions
async function loadPapers() {
    papersList.innerHTML = '<div class="loading">正在加载论文...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/papers/`);
        papers = await res.json();
        renderPapers(papers, papersList);
    } catch (error) {
        papersList.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    }
}

async function loadFavorites() {
    favoritesList.innerHTML = '<div class="loading">正在加载收藏...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/favorites/`);
        const favorites = await res.json();
        
        if (favorites.length === 0) {
            favoritesList.innerHTML = '<div class="empty">暂无收藏</div>';
            return;
        }
        
        const favPapers = favorites.map(f => ({
            ...f.paper,
            is_favorite: true
        }));
        
        renderPapers(favPapers, favoritesList);
    } catch (error) {
        favoritesList.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    }
}

async function searchArxiv() {
    const query = document.getElementById('arxiv-search-input').value.trim();
    if (!query) {
        searchResults.innerHTML = '<div class="empty">请输入搜索关键词</div>';
        return;
    }
    
    searchResults.innerHTML = '<div class="loading">正在搜索...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/search/?q=${encodeURIComponent(query)}&max_results=20`);
        const results = await res.json();
        
        if (!Array.isArray(results) || results.length === 0) {
            searchResults.innerHTML = '<div class="empty">未找到相关论文</div>';
            return;
        }
        
        renderSearchResults(results);
    } catch (error) {
        searchResults.innerHTML = `<div class="error">搜索失败: ${error.message}</div>`;
    }
}

async function downloadPaper(arxivId) {
    try {
        const res = await fetch(`${API_BASE}/papers/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ arxiv_id: arxivId })
        });
        
        if (res.ok) {
            alert('下载成功！');
            loadPapers();
            switchTab('papers');
        } else {
            alert('下载失败');
        }
    } catch (error) {
        alert(`下载失败: ${error.message}`);
    }
}

async function toggleFavorite(paperId) {
    try {
        const res = await fetch(`${API_BASE}/favorites/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paper_id: paperId })
        });
        
        if (res.ok) {
            loadPapers();
            loadFavorites();
        }
    } catch (error) {
        alert(`操作失败: ${error.message}`);
    }
}

async function getPaperDetail(paperId) {
    try {
        const res = await fetch(`${API_BASE}/papers/${paperId}`);
        const paper = await res.json();
        showPaperDetail(paper);
    } catch (error) {
        alert(`加载失败: ${error.message}`);
    }
}

async function summarizePaper(paperId) {
    try {
        const res = await fetch(`${API_BASE}/papers/${paperId}/summarize`);
        const data = await res.json();
        
        if (data.error) {
            alert(data.error);
        } else {
            // Reload and show detail
            await getPaperDetail(paperId);
        }
    } catch (error) {
        alert(`生成摘要失败: ${error.message}`);
    }
}

async function getCode(paperId) {
    try {
        const res = await fetch(`${API_BASE}/papers/${paperId}/code`);
        const data = await res.json();
        return data.repo;
    } catch (error) {
        return null;
    }
}

// Render Functions
function renderPapers(papers, container) {
    if (!papers || papers.length === 0) {
        container.innerHTML = '<div class="empty">暂无论文</div>';
        return;
    }
    
    container.innerHTML = papers.map(paper => `
        <div class="paper-card">
            <h3>${paper.title}</h3>
            <p class="authors">${paper.authors || '未知作者'}</p>
            <div class="meta">
                ${paper.year ? `<span class="year">${paper.year}</span>` : ''}
                ${paper.arxiv_id ? `<span class="arxiv-id">${paper.arxiv_id}</span>` : ''}
            </div>
            <div class="actions">
                <button class="btn-primary btn-small" onclick="viewPaper(${paper.id})">查看</button>
                <button class="btn-secondary btn-small ${paper.is_favorite ? 'active' : ''}" onclick="toggleFavorite(${paper.id})">
                    ${paper.is_favorite ? '★ 已收藏' : '☆ 收藏'}
                </button>
            </div>
        </div>
    `).join('');
}

function renderSearchResults(results) {
    searchResults.innerHTML = results.map(paper => `
        <div class="paper-card">
            <h3>${paper.title}</h3>
            <p class="authors">${paper.authors || '未知作者'}</p>
            <p class="meta">
                <span class="arxiv-id">${paper.arxiv_id}</span>
            </p>
            <div class="actions">
                <button class="btn-primary btn-small" onclick="downloadPaper('${paper.arxiv_id}')">下载</button>
            </div>
        </div>
    `).join('');
}

async function showPaperDetail(paper) {
    let html = `
        <h2>${paper.title}</h2>
        <p class="authors">${paper.authors || '未知作者'}</p>
        <div class="meta">
            ${paper.year ? `<span class="year">${paper.year}</span>` : ''}
            ${paper.arxiv_id ? `<span class="arxiv-id">${paper.arxiv_id}</span>` : ''}
        </div>
    `;
    
    if (paper.abstract) {
        html += `<div class="abstract"><h4>摘要</h4><p>${paper.abstract}</p></div>`;
    }
    
    if (paper.summary) {
        html += `
            <div class="ai-summary">
                <h4>🤖 AI 摘要</h4>
                <p>${paper.summary}</p>
            </div>
        `;
    }
    
    // Get GitHub repo
    const repo = await getCode(paper.id);
    if (repo) {
        html += `<p><a href="${repo}" target="_blank" class="github-link">🔗 查看相关代码</a></p>`;
    }
    
    html += `
        <div class="actions">
            ${paper.pdf_path ? `<a href="/papers/${paper.pdf_path.split('/').pop()}" target="_blank" class="btn-primary btn-small">📄 打开PDF</a>` : ''}
            <button class="btn-secondary btn-small" onclick="summarizePaper(${paper.id})">🤖 生成AI摘要</button>
            <button class="btn-secondary btn-small ${paper.is_favorite ? 'active' : ''}" onclick="toggleFavorite(${paper.id}); getPaperDetail(${paper.id});">
                ${paper.is_favorite ? '★ 已收藏' : '☆ 收藏'}
            </button>
        </div>
    `;
    
    paperDetail.innerHTML = html;
    modal.classList.add('active');
}

function closeModal() {
    modal.classList.remove('active');
}

// Global functions for onclick handlers
window.viewPaper = getPaperDetail;
window.downloadPaper = downloadPaper;
window.toggleFavorite = toggleFavorite;
window.summarizePaper = summarizePaper;
