const saveForm = document.getElementById('saveForm');
const clipboardText = document.getElementById('clipboardText');
const entriesList = document.getElementById('entriesList');
const dateFilter = document.getElementById('dateFilter');
const searchInput = document.getElementById('searchInput');
const showAllBtn = document.getElementById('showAllBtn');
const readClipboardBtn = document.getElementById('readClipboardBtn');

async function fetchEntries(date = '', query = '') {
  const params = new URLSearchParams();

  if (date) params.set('date', date);
  if (query) params.set('q', query);

  const response = await fetch(`/api/entries?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Could not load clipboard entries.');
  }

  return response.json();
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString([], {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function renderEntries(entries) {
  if (!entries.length) {
    entriesList.innerHTML = '<div class="empty-state">No saved messages yet for this filter.</div>';
    return;
  }

  entriesList.innerHTML = entries
    .map(
      (entry) => `
        <article class="entry-card">
          <div class="meta">
            <span>${formatDate(entry.created_at)}</span>
            <span>#${entry.id}</span>
          </div>
          <p class="text">${escapeHtml(entry.text)}</p>
          <div class="entry-actions">
            <button class="copy-btn" type="button" data-copy="${entry.id}">Copy</button>
            <button class="delete-btn" type="button" data-delete="${entry.id}">Delete</button>
          </div>
        </article>
      `
    )
    .join('');
}

function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function loadEntries() {
  try {
    const entries = await fetchEntries(dateFilter.value, searchInput.value.trim());
    renderEntries(entries);
  } catch (error) {
    entriesList.innerHTML = `<div class="empty-state">${error.message}</div>`;
  }
}

async function saveText(text) {
  const trimmedText = text.trim();
  if (!trimmedText) {
    return;
  }

  const response = await fetch('/api/entries', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text: trimmedText }),
  });

  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || 'Unable to save the text.');
  }

  clipboardText.value = '';
  await loadEntries();
}

saveForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  try {
    await saveText(clipboardText.value);
  } catch (error) {
    alert(error.message);
  }
});

readClipboardBtn.addEventListener('click', async () => {
  try {
    if (!navigator.clipboard || !navigator.clipboard.readText) {
      throw new Error('Clipboard access is not available in this browser. Please paste the text manually instead.');
    }

    const text = await navigator.clipboard.readText();
    clipboardText.value = text;
    await saveText(text);
  } catch (error) {
    alert(error.message);
  }
});

dateFilter.addEventListener('change', () => {
  loadEntries();
});

searchInput.addEventListener('input', () => {
  loadEntries();
});

showAllBtn.addEventListener('click', () => {
  dateFilter.value = '';
  searchInput.value = '';
  loadEntries();
});

entriesList.addEventListener('click', async (event) => {
  const deleteTarget = event.target.closest('[data-delete]');
  const copyTarget = event.target.closest('[data-copy]');

  if (deleteTarget) {
    const id = deleteTarget.getAttribute('data-delete');
    const response = await fetch(`/api/entries/${id}`, { method: 'DELETE' });

    if (response.ok) {
      await loadEntries();
    }
    return;
  }

  if (copyTarget) {
    const entryId = Number(copyTarget.getAttribute('data-copy'));
    const entry = (await fetchEntries(dateFilter.value, searchInput.value.trim())).find((item) => item.id === entryId);

    if (entry && navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(entry.text);
    }
  }
});

loadEntries();
