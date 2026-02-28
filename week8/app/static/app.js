// OS Paper Hub - Frontend JavaScript
const API_BASE = '/api';

let papers = [];
let currentPaperIdForChat = null;

const papersList = document.getElementById('papers-list');
const searchResults = document.getElementById('search-results');
const modal = document.getElementById('paper-modal');
const paperDetail = document.getElementById('paper-detail');
const stationChatMessages = document.getElementById('station-chat-messages');
const stationChatInput = document.getElementById('station-chat-input');
const stationChatSend = document.getElementById('station-chat-send');

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadPapers();
    initStationChat();
});

function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            switchTab(tabId);
        });
    });
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
    document.querySelector('.close').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
}

function switchTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    const tabEl = document.querySelector(`[data-tab="${tabId}"]`);
    if (tabEl) tabEl.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    const content = document.getElementById(`${tabId}-tab`);
    if (content) content.classList.add('active');
}

const PAPERS_LOAD_TIMEOUT_MS = 15000;

async function loadPapers() {
    papersList.innerHTML = '<div class="loading">正在加载论文...</div>';
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), PAPERS_LOAD_TIMEOUT_MS);
    try {
        const res = await fetch(`${API_BASE}/papers/`, { signal: controller.signal });
        clearTimeout(timeoutId);
        papers = await res.json();
        renderPapersList(papers);
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            papersList.innerHTML = `
                <div class="error">
                    加载超时（${PAPERS_LOAD_TIMEOUT_MS / 1000} 秒）。请检查网络或刷新后重试。
                    <button class="btn-primary btn-small" style="margin-top:12px" onclick="loadPapers()">重试</button>
                </div>`;
        } else {
            papersList.innerHTML = `
                <div class="error">加载失败: ${escapeHtml(error.message)}
                <button class="btn-primary btn-small" style="margin-top:12px" onclick="loadPapers()">重试</button>
                </div>`;
        }
    }
}

function renderPapersList(papersData) {
    if (!papersData || papersData.length === 0) {
        papersList.innerHTML = '<div class="empty">暂无论文</div>';
        return;
    }
    papersList.innerHTML = `
        <table class="papers-table">
            <thead><tr><th>标题</th><th>作者</th><th>年份</th></tr></thead>
            <tbody>
                ${papersData.map(p => {
                    const pdfUrl = p.pdf_path ? '/papers/' + encodeURIComponent(p.pdf_path.split('/').pop()) : null;
                    const rowClick = pdfUrl
                        ? `onclick="window.open('${pdfUrl}', '_blank')"`
                        : `onclick="viewPaper(${p.id})"`;
                    return `<tr ${rowClick} class="row-clickable">
                        <td class="col-title">${escapeHtml(p.title || '')}</td>
                        <td class="col-authors">${escapeHtml(p.authors || '—')}</td>
                        <td class="col-year">${p.year || '—'}</td>
                    </tr>`;
                }).join('')}
            </tbody>
        </table>
    `;
}

function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
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
        const data = await res.json();
        if (!res.ok || (data.error && !Array.isArray(data))) {
            searchResults.innerHTML = `<div class="error">${data.detail || data.error || '搜索失败'}</div>`;
            return;
        }
        const results = Array.isArray(data) ? data : [];
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="empty">未找到相关论文</div>';
            return;
        }
        const yearFrom = (pub) => (pub && pub.substring) ? pub.substring(0, 4) : null;
        searchResults.innerHTML = `
            <table class="papers-table">
                <thead><tr><th>标题</th><th>作者</th><th>年份</th><th></th></thead>
                <tbody>
                    ${results.map(p => `
                        <tr>
                            <td class="col-title">${escapeHtml(p.title || '')}</td>
                            <td class="col-authors">${escapeHtml(p.authors || '—')}</td>
                            <td class="col-year">${yearFrom(p.published) || yearFrom(p.year) || '—'}</td>
                            <td><button class="btn-download" onclick="event.stopPropagation(); downloadPaper('${(p.arxiv_id || '').replace(/'/g, "\\'")}')">下载</button></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
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
            alert('下载成功');
            loadPapers();
            switchTab('papers');
        } else {
            const d = await res.json().catch(() => ({}));
            alert(d.detail || '下载失败');
        }
    } catch (error) {
        alert('下载失败: ' + error.message);
    }
}

async function getPaperDetail(paperId) {
    try {
        const res = await fetch(`${API_BASE}/papers/${paperId}`);
        const paper = await res.json();
        showPaperDetail(paper);
    } catch (error) {
        alert('加载失败: ' + error.message);
    }
}

async function summarizePaper(paperId, btnEl) {
    const wrap = document.getElementById('summary-area');
    if (wrap) {
        wrap.innerHTML = '<div class="loading-inline">生成中…</div>';
    }
    if (btnEl) {
        btnEl.disabled = true;
        btnEl.textContent = '生成中…';
    }
    try {
        const res = await fetch(`${API_BASE}/papers/${paperId}/summarize`);
        const data = await res.json();
        if (wrap) {
            if (data.error) {
                wrap.innerHTML = `<div class="error-inline">${escapeHtml(data.error)}</div>`;
            } else if (data.summary) {
                wrap.innerHTML = `<div class="ai-summary"><h4>🤖 AI 摘要</h4><p>${escapeHtml(data.summary)}</p></div>`;
            } else {
                wrap.innerHTML = '<div class="error-inline">生成失败</div>';
            }
        }
    } catch (error) {
        if (wrap) wrap.innerHTML = `<div class="error-inline">${escapeHtml(error.message)}</div>`;
    }
    if (btnEl) {
        btnEl.disabled = false;
        btnEl.textContent = '🤖 生成AI摘要';
    }
}

async function getCode(paperId) {
    try {
        const res = await fetch(`${API_BASE}/papers/${paperId}/code`);
        const data = await res.json();
        return data.repo || null;
    } catch (_) {
        return null;
    }
}

async function showPaperDetail(paper) {
    currentPaperIdForChat = paper.id;
    let html = `
        <h2>${escapeHtml(paper.title)}</h2>
        <p class="authors">${paper.authors || '未知作者'}</p>
        <div class="meta">
            ${paper.year ? `<span class="year">${paper.year}</span>` : ''}
            ${paper.arxiv_id ? `<span class="arxiv-id">${paper.arxiv_id}</span>` : ''}
        </div>
    `;
    if (paper.abstract) {
        html += `<div class="abstract"><h4>摘要</h4><p>${escapeHtml(paper.abstract)}</p></div>`;
    }
    html += `<div id="summary-area">`;
    if (paper.summary) {
        html += `<div class="ai-summary"><h4>🤖 AI 摘要</h4><p>${escapeHtml(paper.summary)}</p></div>`;
    } else {
        html += `<div class="summary-actions">
            <button class="btn-secondary btn-small" id="btn-summarize" onclick="summarizePaper(${paper.id}, this)">🤖 生成AI摘要</button>
        </div>`;
    }
    html += `</div>`;

    const repo = await getCode(paper.id);
    if (repo) {
        html += `<p><a href="${escapeHtml(repo)}" target="_blank" class="github-link">🔗 查看相关代码</a></p>`;
    }
    html += `
        <div class="actions">
            ${paper.pdf_path ? `<a href="/papers/${escapeHtml(paper.pdf_path.split('/').pop())}" target="_blank" class="btn-primary btn-small">📄 打开PDF</a>` : ''}
        </div>
        <div class="paper-chat-section">
            <h4>基于本文的问答</h4>
            <div id="paper-chat-messages" class="chat-messages"></div>
            <div class="chat-input-row">
                <input type="text" id="paper-chat-input" placeholder="针对这篇论文提问（需已下载到本地）...">
                <button id="paper-chat-send" class="btn-primary">发送</button>
            </div>
        </div>
    `;
    paperDetail.innerHTML = html;
    modal.classList.add('active');
    initPaperChat(paper.id);
}

function initPaperChat(paperId) {
    const input = document.getElementById('paper-chat-input');
    const sendBtn = document.getElementById('paper-chat-send');
    const messagesEl = document.getElementById('paper-chat-messages');
    if (!input || !sendBtn || !messagesEl) return;
    sendBtn.onclick = () => sendPaperChat(paperId, input, messagesEl);
    input.onkeypress = (e) => { if (e.key === 'Enter') sendPaperChat(paperId, input, messagesEl); };
}

async function sendPaperChat(paperId, inputEl, messagesEl) {
    const msg = inputEl.value.trim();
    if (!msg) return;
    appendChatMessage(messagesEl, 'user', msg);
    inputEl.value = '';
    appendChatMessage(messagesEl, 'assistant', '(正在生成…)');
    try {
        const res = await fetch(`${API_BASE}/papers/${paperId}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        const last = messagesEl.querySelector('.msg-assistant:last-child');
        if (last) last.remove();
        if (!res.ok) {
            appendChatMessage(messagesEl, 'assistant', `错误: ${data.detail || res.statusText}`);
        } else {
            appendChatMessage(messagesEl, 'assistant', data.reply || '(无回复)');
        }
    } catch (error) {
        const last = messagesEl.querySelector('.msg-assistant:last-child');
        if (last) last.remove();
        appendChatMessage(messagesEl, 'assistant', '请求失败: ' + error.message);
    }
}

function initStationChat() {
    if (!stationChatSend || !stationChatInput) return;
    stationChatSend.onclick = () => sendStationChat();
    stationChatInput.onkeypress = (e) => { if (e.key === 'Enter') sendStationChat(); };
}

async function sendStationChat() {
    const msg = stationChatInput.value.trim();
    if (!msg) return;
    appendChatMessage(stationChatMessages, 'user', msg);
    stationChatInput.value = '';
    appendChatMessage(stationChatMessages, 'assistant', '(正在生成…)');
    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        const last = stationChatMessages.querySelector('.msg-assistant:last-child');
        if (last) last.remove();
        if (!res.ok) {
            appendChatMessage(stationChatMessages, 'assistant', `错误: ${data.detail || res.statusText}`);
        } else {
            appendChatMessage(stationChatMessages, 'assistant', data.reply || '(无回复)');
        }
    } catch (error) {
        const last = stationChatMessages.querySelector('.msg-assistant:last-child');
        if (last) last.remove();
        appendChatMessage(stationChatMessages, 'assistant', '请求失败: ' + error.message);
    }
}

function appendChatMessage(container, role, text) {
    const div = document.createElement('div');
    div.className = `chat-msg msg-${role}`;
    div.innerHTML = `<span class="chat-role">${role === 'user' ? '我' : 'Ollama'}</span><span class="chat-text">${escapeHtml(text)}</span>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function closeModal() {
    modal.classList.remove('active');
    currentPaperIdForChat = null;
}

window.viewPaper = getPaperDetail;
window.downloadPaper = downloadPaper;
window.summarizePaper = summarizePaper;
