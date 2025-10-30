// Global state
let allItems = [];
let filteredItems = [];
let currentPage = 1;
let itemsPerPage = 20;
let sortOrder = 'asc';
let compareItems = [];
let selectedItem = null;
let notes = {};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadNotes();
    loadItems();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('searchInput').addEventListener('input', debounce(filterAndRender, 300));
    document.getElementById('categorySelect').addEventListener('change', filterAndRender);
    document.getElementById('sortSelect').addEventListener('change', filterAndRender);
    document.getElementById('sortOrderBtn').addEventListener('click', toggleSortOrder);
    document.getElementById('randomBtn').addEventListener('click', selectRandomItem);
    document.getElementById('exportJsonBtn').addEventListener('click', () => exportData('json'));
    document.getElementById('exportCsvBtn').addEventListener('click', () => exportData('csv'));
    document.getElementById('reloadBtn').addEventListener('click', reloadData);
    document.getElementById('prevBtn').addEventListener('click', () => changePage(-1));
    document.getElementById('nextBtn').addEventListener('click', () => changePage(1));
    document.getElementById('clearCompareBtn').addEventListener('click', clearCompare);
}

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        const select = document.getElementById('categorySelect');
        select.innerHTML = categories.map(cat => 
            `<option value="${cat}">${cat.charAt(0).toUpperCase() + cat.slice(1)}</option>`
        ).join('');
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadNotes() {
    try {
        const response = await fetch('/api/notes');
        notes = await response.json();
    } catch (error) {
        console.error('Error loading notes:', error);
    }
}

async function saveNotes() {
    try {
        await fetch('/api/notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(notes)
        });
        alert('Note saved successfully!');
    } catch (error) {
        console.error('Error saving notes:', error);
        alert('Failed to save note');
    }
}

async function loadItems() {
    const params = new URLSearchParams({
        search: document.getElementById('searchInput').value,
        category: document.getElementById('categorySelect').value,
        sort: document.getElementById('sortSelect').value,
        order: sortOrder,
        page: currentPage,
        per_page: itemsPerPage
    });

    try {
        const response = await fetch(`/api/items?${params}`);
        const data = await response.json();
        filteredItems = data.items;
        renderItems();
        renderPagination(data.page, data.total_pages);
        updateStats(data.total);
    } catch (error) {
        console.error('Error loading items:', error);
    }
}

function renderItems() {
    const container = document.getElementById('itemsContainer');
    container.innerHTML = filteredItems.map(item => `
        <div class="item-card ${selectedItem?.name === item.name ? 'selected' : ''}" 
             onclick="selectItem('${escapeHtml(item.name)}')">
            <button class="compare-btn ${compareItems.find(i => i.name === item.name) ? 'active' : ''}"
                    onclick="event.stopPropagation(); toggleCompare('${escapeHtml(item.name)}')">
                Compare
            </button>
            <h3>${escapeHtml(item.name)}</h3>
            <div class="item-type">${escapeHtml(item.infobox?.type || 'Unknown Type')}</div>
            <div class="item-stats">
                ${item.infobox?.base_dps ? `<span>DPS: ${escapeHtml(item.infobox.base_dps)}</span>` : ''}
                ${item.infobox?.money_cost ? `<span>Price: ${escapeHtml(item.infobox.money_cost)}</span>` : ''}
            </div>
        </div>
    `).join('');
}

function renderPagination(page, totalPages) {
    document.getElementById('pageInfo').textContent = `Page ${page} of ${totalPages}`;
    document.getElementById('prevBtn').disabled = page === 1;
    document.getElementById('nextBtn').disabled = page === totalPages;
}

function updateStats(total) {
    document.getElementById('stats').innerHTML = `
        <span>Filtered: ${total} items</span>
        <span>Page ${currentPage}</span>
    `;
}

async function selectItem(itemName) {
    try {
        const response = await fetch(`/api/item/${encodeURIComponent(itemName)}`);
        selectedItem = await response.json();
        renderDetail();
        renderItems(); // Re-render to update selected state
    } catch (error) {
        console.error('Error loading item:', error);
    }
}

function renderDetail() {
    if (!selectedItem) {
        document.getElementById('detailContent').innerHTML = '<p class="detail-empty">Select an item to view details</p>';
        return;
    }

    const stats = Object.entries(selectedItem.infobox || {})
        .filter(([key]) => key !== 'internal_name')
        .map(([key, value]) => `
            <div class="stat-row">
                <span class="label">${formatLabel(key)}:</span>
                <span class="value">${escapeHtml(value)}</span>
            </div>
        `).join('');

    document.getElementById('detailContent').innerHTML = `
        <h2>${escapeHtml(selectedItem.name)}</h2>
        <div class="stats-container">
            ${stats}
        </div>
        <div class="description">
            <h3>Description</h3>
            <p>${escapeHtml(selectedItem.long_description?.substring(0, 500) || 'No description available')}</p>
        </div>
        ${selectedItem.url ? `<a href="${selectedItem.url}" target="_blank" class="wiki-link">View on Wiki →</a>` : ''}
        <div class="notes-section">
            <h3>Personal Notes</h3>
            <textarea id="noteText">${notes[selectedItem.name] || ''}</textarea>
            <button onclick="saveNote()">💾 Save Note</button>
        </div>
    `;
}

function saveNote() {
    if (selectedItem) {
        const noteText = document.getElementById('noteText').value;
        notes[selectedItem.name] = noteText;
        saveNotes();
    }
}

function toggleCompare(itemName) {
    const item = filteredItems.find(i => i.name === itemName);
    if (!item) return;

    const index = compareItems.findIndex(i => i.name === itemName);
    if (index > -1) {
        compareItems.splice(index, 1);
    } else if (compareItems.length < 3) {
        compareItems.push(item);
    }

    renderCompare();
    renderItems();
}

function renderCompare() {
    const bar = document.getElementById('compareBar');
    const container = document.getElementById('compareItems');
    
    if (compareItems.length === 0) {
        bar.style.display = 'none';
        return;
    }

    bar.style.display = 'block';
    document.getElementById('compareCount').textContent = compareItems.length;
    
    container.innerHTML = compareItems.map(item => `
        <div class="compare-item">
            <button class="remove-btn" onclick="toggleCompare('${escapeHtml(item.name)}')">×</button>
            <h4>${escapeHtml(item.name)}</h4>
            ${item.infobox?.base_dps ? `<div>DPS: ${escapeHtml(item.infobox.base_dps)}</div>` : ''}
            ${item.infobox?.money_cost ? `<div>Price: ${escapeHtml(item.infobox.money_cost)}</div>` : ''}
            ${item.infobox?.scaling ? `<div>Scales: ${escapeHtml(item.infobox.scaling)}</div>` : ''}
        </div>
    `).join('');
}

function clearCompare() {
    compareItems = [];
    renderCompare();
    renderItems();
}

async function selectRandomItem() {
    try {
        const response = await fetch('/api/random');
        selectedItem = await response.json();
        renderDetail();
    } catch (error) {
        console.error('Error getting random item:', error);
    }
}

function toggleSortOrder() {
    sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    loadItems();
}

function changePage(delta) {
    currentPage += delta;
    loadItems();
}

function filterAndRender() {
    currentPage = 1;
    loadItems();
}

async function exportData(format) {
    const params = new URLSearchParams({
        search: document.getElementById('searchInput').value,
        category: document.getElementById('categorySelect').value
    });
    
    window.location.href = `/api/export/${format}?${params}`;
}

async function reloadData() {
    try {
        const response = await fetch('/api/reload');
        const data = await response.json();
        if (data.success) {
            alert(`Reloaded ${data.count} items`);
            loadItems();
        }
    } catch (error) {
        console.error('Error reloading data:', error);
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function formatLabel(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
```

### 5. **requirements.txt** (Python Dependencies)
```
Flask==3.0.0
