async function loadBrief() {
  const state7dEl = document.getElementById("state-7d");
  const cards7dEl = document.getElementById("cards-7d");
  const state30dEl = document.getElementById("state-30d");
  const cards30dEl = document.getElementById("cards-30d");
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
    metaEl.textContent = `日期 ${data.date} · 更新于 ${new Date(data.generated_at).toLocaleString()}`;

    renderCards(data.repos_7d, cards7dEl, state7dEl);
    renderCards(data.repos_30d, cards30dEl, state30dEl);
  } catch (_err) {
    clearTimeout(timeoutId);
    cards7dEl.hidden = true;
    state7dEl.hidden = false;
    state7dEl.textContent = "趋势数据加载失败，请稍后刷新";
    cards30dEl.hidden = true;
    state30dEl.hidden = false;
    state30dEl.textContent = "趋势数据加载失败，请稍后刷新";
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
          <span>语言: ${repo.language || "Unknown"}</span>
          <span>Stars: ${repo.stars_today}</span>
          <span>7天增星: ${repo.weekly_star_gain}</span>
          <span>30天增星: ${repo.monthly_star_gain}</span>
          <span>Forks: ${repo.forks}</span>
        </div>
        <p class="reason">推荐理由: ${repo.reason}</p>
      </article>
    `
    )
    .join("");

  cardsEl.hidden = false;
  stateEl.hidden = true;
}

loadBrief();
