async function fetchJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function loadNotes() {
  const list = document.getElementById('notes');
  list.innerHTML = '';
  const notes = await fetchJSON('/notes/');
  for (const n of notes) {
    const li = document.createElement('li');
    li.textContent = `${n.title}: ${n.content}`;
    list.appendChild(li);
  }
}

let currentActionFilter = 'all'; // 'all' | 'open' | 'done'
let selectedActionIds = new Set();

function updateBulkButtonState() {
  const bulkBtn = document.getElementById('bulk-complete');
  bulkBtn.disabled = selectedActionIds.size === 0;
}

function buildActionsUrl() {
  if (currentActionFilter === 'open') return '/action-items?completed=false';
  if (currentActionFilter === 'done') return '/action-items?completed=true';
  return '/action-items/';
}

async function loadActions() {
  const list = document.getElementById('actions');
  list.innerHTML = '';
  selectedActionIds = new Set();
  updateBulkButtonState();

  const items = await fetchJSON(buildActionsUrl());
  for (const a of items) {
    const li = document.createElement('li');
    const label = document.createElement('span');
    label.textContent = `${a.description} [${a.completed ? 'done' : 'open'}]`;

    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.style.marginRight = '0.5rem';
    checkbox.onchange = () => {
      if (checkbox.checked) {
        selectedActionIds.add(a.id);
      } else {
        selectedActionIds.delete(a.id);
      }
      updateBulkButtonState();
    };

    li.appendChild(checkbox);
    li.appendChild(label);

    if (!a.completed) {
      const btn = document.createElement('button');
      btn.textContent = 'Complete';
      btn.onclick = async () => {
        await fetchJSON(`/action-items/${a.id}/complete`, { method: 'PUT' });
        loadActions();
      };
      li.appendChild(btn);
    }
    list.appendChild(li);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('note-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = document.getElementById('note-title').value;
    const content = document.getElementById('note-content').value;
    await fetchJSON('/notes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    });
    e.target.reset();
    loadNotes();
  });

  document.getElementById('action-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const description = document.getElementById('action-desc').value;
    await fetchJSON('/action-items/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    e.target.reset();
    loadActions();
  });

  document
    .getElementById('action-filters')
    .addEventListener('click', (event) => {
      const target = event.target;
      if (!(target instanceof HTMLButtonElement)) return;
      const value = target.getAttribute('data-filter');
      if (!value) return;
      currentActionFilter = value;

      document
        .querySelectorAll('#action-filters button')
        .forEach((btn) => btn.removeAttribute('data-active'));
      target.setAttribute('data-active', 'true');

      loadActions();
    });

  document.getElementById('bulk-complete').addEventListener('click', async () => {
    if (selectedActionIds.size === 0) return;
    const ids = Array.from(selectedActionIds);
    await fetchJSON('/action-items/bulk-complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ids),
    });
    await loadActions();
  });

  loadNotes();
  loadActions();
});
