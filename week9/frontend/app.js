async function loadBrief() {
  const state7dEl = document.getElementById("state-7d");
  const cards7dEl = document.getElementById("cards-7d");
  const state30dEl = document.getElementById("state-30d");
  const cards30dEl = document.getElementById("cards-30d");
  const stateAgentEl = document.getElementById("state-agent");
  const cardsAgentEl = document.getElementById("cards-agent");
  const metaEl = document.getElementById("meta");
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  try {
    const res = await fetch("/api/trending/today", { signal: controller.signal });
    clearTimeout(timeoutId);
    if (!res.ok) {
      throw new Error("upstream_failed");
    }

    const data = await res.json();
    const updatedAt = data.generated_at
      ? new Date(data.generated_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })
      : "";
    metaEl.textContent = `📅 ${data.date} · 更新时间 ${updatedAt}`;

    renderCards(data.repos_7d, cards7dEl, state7dEl);
    renderCards(data.repos_30d, cards30dEl, state30dEl);
    renderAgentCards(data.repos_agent, cardsAgentEl, stateAgentEl);
  } catch (_err) {
    clearTimeout(timeoutId);
    cards7dEl.hidden = true;
    state7dEl.hidden = false;
    state7dEl.textContent = "趋势数据加载失败，请稍后刷新";
    cards30dEl.hidden = true;
    state30dEl.hidden = false;
    state30dEl.textContent = "趋势数据加载失败，请稍后刷新";
    cardsAgentEl.hidden = true;
    stateAgentEl.hidden = false;
    stateAgentEl.textContent = "Agent数据加载失败，请稍后刷新";
    metaEl.textContent = "当前仅展示7天新增星榜单";
  }
}

function renderCards(repos, cardsEl, stateEl) {
  if (!repos || !repos.length) {
    stateEl.hidden = false;
    stateEl.textContent = "暂无数据";
    cardsEl.hidden = true;
    return;
  }

  cardsEl.innerHTML = repos
    .map(
      (repo, idx) => `
      <article class="card">
        <h2>${idx + 1}. <a href="${repo.repo_url}" target="_blank" rel="noreferrer">${repo.full_name}</a></h2>
        <p class="desc">${repo.description || "暂无描述"}</p>
        <div class="metrics">
          <span>⭐ ${repo.stars_today}</span>
          <span>🔥 +${repo.weekly_star_gain}/7d</span>
          <span>📈 +${repo.monthly_star_gain}/30d</span>
          <span>🍴 ${repo.forks}</span>
        </div>
        <div class="meta-info">
          <span>语言: ${repo.language || "Unknown"}</span>
          <span>创建: ${repo.created_at}</span>
        </div>
        <p class="reason">💡 ${repo.reason}</p>
      </article>
    `
    )
    .join("");

  cardsEl.hidden = false;
  stateEl.hidden = true;
}

function renderAgentCards(repos, cardsEl, stateEl) {
  if (!repos || !repos.length) {
    stateEl.hidden = false;
    stateEl.textContent = "暂无Agent相关项目";
    cardsEl.hidden = true;
    return;
  }

  cardsEl.innerHTML = repos
    .map(
      (repo, idx) => `
      <article class="card">
        <h2>${idx + 1}. <a href="${repo.repo_url}" target="_blank" rel="noreferrer">${repo.full_name}</a></h2>
        <p class="desc">${repo.description || "暂无描述"}</p>
        <div class="metrics">
          <span>⭐ ${repo.stars_today}</span>
          <span>🍴 ${repo.forks}</span>
        </div>
        <div class="meta-info">
          <span>语言: ${repo.language || "Unknown"}</span>
          <span>创建: ${repo.created_at}</span>
        </div>
        <div class="topics">
          ${(repo.topics || []).map(t => `<span class="topic">${t}</span>`).join("")}
        </div>
      </article>
    `
    )
    .join("");

  cardsEl.hidden = false;
  stateEl.hidden = true;
}

loadBrief();
