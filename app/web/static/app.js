/**
 * Library Studio - Premium Frontend Logic
 * Senior Implementation: Async/Await, Clean Architecture, Reactive State
 */

const apiBase = window.APP_CONFIG?.apiBase || "/api/v1";
const bookEndpoint = `${apiBase}/books/`;

// Visual Config & Status Labels
const STATUS_META = {
    available: { label: "Disponível", class: "available" },
    borrowed: { label: "Emprestado", class: "borrowed" },
    reserved: { label: "Reservado", class: "reserved" },
    maintenance: { label: "Manutenção", class: "maintenance" },
};

const state = {
    books: [],
    selectedId: null,
    total: 0,
    isEditing: false,
    filters: {
        q: "",
        author: "",
        yearMin: "",
        yearMax: "",
        sort: "created_at",
        order: "desc",
        limit: 20,
    },
};

// DOM Elements Repository
const els = {
    // Basic List Elements
    list: document.getElementById("book-list"),
    listStatus: document.getElementById("list-state"),
    resultCount: document.getElementById("result-count"),
    
    // Filters
    searchInput: document.getElementById("search-input"),
    authorInput: document.getElementById("author-input"),
    yearMin: document.getElementById("year-min"),
    yearMax: document.getElementById("year-max"),
    sortSelect: document.getElementById("sort-select"),
    orderSelect: document.getElementById("order-select"),
    limitSelect: document.getElementById("limit-select"),
    
    // Actions
    refreshBtn: document.getElementById("refresh-btn"),
    seedBtn: document.getElementById("seed-btn"),
    clearBtn: document.getElementById("clear-btn"),
    
    // Stats
    statTotal: document.getElementById("stat-total"),
    statLatest: document.getElementById("stat-latest"),
    statIsbn: document.getElementById("stat-isbn"),
    
    // Inspector Details
    inspector: document.getElementById("inspector"),
    inspectorPlaceholder: document.getElementById("inspector-placeholder"),
    inspectorContent: document.getElementById("inspector-content"),
    detailTitle: document.getElementById("detail-title"),
    detailAuthor: document.getElementById("detail-author"),
    detailStatus: document.getElementById("detail-status"),
    detailYear: document.getElementById("detail-year"),
    detailIsbn: document.getElementById("detail-isbn"),
    detailId: document.getElementById("detail-id"),
    detailDesc: document.getElementById("detail-description-text"),
    detailCoverImg: document.getElementById("detail-cover-img"),
    detailCoverFallback: document.getElementById("detail-cover-fallback"),
    selectedPill: document.getElementById("selected-pill"),
    
    // Form Elements
    bookForm: document.getElementById("book-form"),
    formTitle: document.getElementById("form-title"),
    submitBtn: document.getElementById("submit-btn"),
    submitBtnText: document.querySelector("#submit-btn span"),
    cancelEditBtn: document.getElementById("cancel-edit-btn"),
    lookupBtn: document.getElementById("lookup-btn"),
    
    // Form Inputs
    formId: document.getElementById("form-book-id"),
    formIsbn: document.getElementById("form-isbn"),
    formTitleInput: document.getElementById("form-title-input"),
    formAuthorInput: document.getElementById("form-author-input"),
    formYearInput: document.getElementById("form-year-input"),
    formStatusInput: document.getElementById("form-status-input"),
    formDescInput: document.getElementById("form-desc-input"),
    
    // Misc
    toastContainer: document.getElementById("toast-container"),
    deleteBtn: document.getElementById("delete-btn"),
    editModeBtn: document.getElementById("edit-mode-btn"),
};

/**
 * UTILS
 */
const debounce = (fn, wait = 400) => {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), wait);
    };
};

const showToast = (message, type = "success") => {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    const icon = type === "success" ? "check-circle" : (type === "error" ? "alert-circle" : "info");
    toast.innerHTML = `<i data-lucide="${icon}"></i> <span>${message}</span>`;
    
    els.toastContainer.appendChild(toast);
    lucide.createIcons();
    
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => toast.remove(), 400);
    }, 4000);
};

/**
 * API CALLS
 */
const fetchBooks = async () => {
    els.listStatus.classList.remove("hidden");
    
    const params = new URLSearchParams();
    if (state.filters.q.trim()) params.set("q", state.filters.q.trim());
    if (state.filters.author.trim()) params.set("author", state.filters.author.trim());
    if (state.filters.yearMin) params.set("year_min", state.filters.yearMin);
    if (state.filters.yearMax) params.set("year_max", state.filters.yearMax);
    params.set("limit", state.filters.limit);
    params.set("sort", state.filters.sort);
    params.set("order", state.filters.order);

    try {
        const response = await fetch(`${bookEndpoint}?${params}`);
        if (!response.ok) throw new Error("Erro ao carregar acervo.");
        
        const data = await response.json();
        state.books = data;
        state.total = parseInt(response.headers.get("X-Total-Count") || data.length);
        
        renderBooks();
        renderStats();
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        els.listStatus.classList.add("hidden");
    }
};

const createOrUpdateBook = async (payload) => {
    const isEditing = !!payload.id;
    const url = isEditing ? `${bookEndpoint}${payload.id}` : bookEndpoint;
    const method = isEditing ? "PUT" : "POST";

    const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Erro ao salvar livro.");
    }
    return response.json();
};

const deleteBook = async (id) => {
    const response = await fetch(`${bookEndpoint}${id}`, { method: "DELETE" });
    if (!response.ok) throw new Error("Erro ao excluir livro.");
};

const lookupISBN = async (isbn) => {
    const response = await fetch(`${apiBase}/books/lookup/${isbn}`);
    if (!response.ok) throw new Error("ISBN não encontrado ou falha na API externa.");
    return response.json();
};

/**
 * RENDERING
 */
const renderBooks = () => {
    els.list.innerHTML = "";
    els.resultCount.textContent = `${state.total} resultados`;

    state.books.forEach((book, index) => {
        const item = document.createElement("div");
        item.className = `book-item ${book.id === state.selectedId ? "active" : ""}`;
        item.style.animationDelay = `${index * 0.05}s`;
        
        const statusCfg = STATUS_META[book.status] || STATUS_META.available;
        
        item.innerHTML = `
            <div class="book-main-info">
                <span class="book-title">${book.title}</span>
                <span class="book-author">${book.author}</span>
            </div>
            <div class="book-meta">
                <span class="book-year">${book.year || "-"}</span>
                <div class="status-dot ${statusCfg.class}" title="${statusCfg.label}"></div>
            </div>
        `;
        
        item.onclick = () => selectBook(book);
        els.list.appendChild(item);
    });
};

const renderStats = () => {
    els.statTotal.textContent = state.total;
    const years = state.books.map(b => b.year).filter(y => y > 0);
    els.statLatest.textContent = years.length ? Math.max(...years) : "-";
    els.statIsbn.textContent = state.books.filter(b => b.isbn).length;
};

const selectBook = (book) => {
    state.selectedId = book.id;
    
    // UI Updates
    els.inspectorPlaceholder.classList.add("hidden");
    els.inspectorContent.classList.remove("hidden");
    els.selectedPill.classList.remove("hidden");
    
    els.detailTitle.textContent = book.title;
    els.detailAuthor.textContent = book.author;
    els.detailYear.textContent = book.year || "-";
    els.detailIsbn.textContent = book.isbn || "-";
    els.detailId.textContent = `#${book.id}`;
    els.detailDesc.textContent = book.description || "Nenhuma descrição disponível para este volume.";
    
    const statusCfg = STATUS_META[book.status] || STATUS_META.available;
    els.detailStatus.textContent = statusCfg.label;
    els.detailStatus.className = `status-tag ${statusCfg.class}`;
    
    if (book.cover_url) {
        els.detailCoverImg.src = book.cover_url;
        els.detailCoverImg.classList.remove("hidden");
        els.detailCoverFallback.classList.add("hidden");
    } else {
        els.detailCoverImg.classList.add("hidden");
        els.detailCoverFallback.classList.remove("hidden");
    }

    renderBooks();
    
    // If we were editing another book, reset form to normal
    if (state.isEditing) exitEditMode();
};

const enterEditMode = () => {
    const book = state.books.find(b => b.id === state.selectedId);
    if (!book) return;

    state.isEditing = true;
    els.formTitle.textContent = "Editar Registro";
    els.submitBtnText.textContent = "Atualizar Livro";
    els.cancelEditBtn.classList.remove("hidden");
    
    // Fill Form
    els.formId.value = book.id;
    els.formIsbn.value = book.isbn || "";
    els.formTitleInput.value = book.title;
    els.formAuthorInput.value = book.author;
    els.formYearInput.value = book.year || "";
    els.formStatusInput.value = book.status;
    els.formDescInput.value = book.description || "";
    
    els.formIsbn.focus();
    showToast("Modo de edição ativado.", "info");
};

const exitEditMode = () => {
    state.isEditing = false;
    els.formTitle.textContent = "Novo Registro";
    els.submitBtnText.textContent = "Salvar Registro";
    els.cancelEditBtn.classList.add("hidden");
    els.bookForm.reset();
    els.formId.value = "";
};

/**
 * EVENT LISTENERS
 */
els.refreshBtn.onclick = () => fetchBooks();

els.seedBtn.onclick = async () => {
    const examples = [
        { title: "Clean Code", author: "Robert C. Martin", year: 2008, isbn: "0132350882", status: "available" },
        { title: "Pragmatic Programmer", author: "Andrew Hunt", year: 1999, isbn: "020161622X", status: "available" }
    ];
    try {
        for (const ex of examples) await createOrUpdateBook(ex);
        showToast("Exemplos criados!");
        fetchBooks();
    } catch (err) {
        showToast(err.message, "error");
    }
};

els.clearBtn.onclick = () => {
    els.searchInput.value = "";
    els.authorInput.value = "";
    els.yearMin.value = "";
    els.yearMax.value = "";
    state.filters = { ...state.filters, q: "", author: "", yearMin: "", yearMax: "" };
    fetchBooks();
};

const updateFilter = (key, value) => {
    state.filters[key] = value;
    fetchBooks();
};

els.searchInput.oninput = debounce(e => updateFilter("q", e.target.value));
els.authorInput.oninput = debounce(e => updateFilter("author", e.target.value));
els.yearMin.onchange = e => updateFilter("yearMin", e.target.value);
els.yearMax.onchange = e => updateFilter("yearMax", e.target.value);
els.sortSelect.onchange = e => updateFilter("sort", e.target.value);
els.orderSelect.onchange = e => updateFilter("order", e.target.value);
els.limitSelect.onchange = e => updateFilter("limit", parseInt(e.target.value));

els.bookForm.onsubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData(els.bookForm);
    const payload = Object.fromEntries(formData.entries());
    
    // Clean payload
    if (!payload.id) delete payload.id;
    if (!payload.year) delete payload.year;
    else payload.year = parseInt(payload.year);
    
    try {
        const saved = await createOrUpdateBook(payload);
        showToast(payload.id ? "Registro atualizado!" : "Livro cadastrado!");
        exitEditMode();
        await fetchBooks();
        selectBook(saved);
    } catch (err) {
        showToast(err.message, "error");
    }
};

els.cancelEditBtn.onclick = exitEditMode;

els.editModeBtn.onclick = enterEditMode;

els.deleteBtn.onclick = async () => {
    if (!state.selectedId) return;
    if (!confirm("Tem certeza que deseja excluir este registro?")) return;
    
    try {
        await deleteBook(state.selectedId);
        showToast("Registro removido.");
        state.selectedId = null;
        els.inspectorContent.classList.add("hidden");
        els.inspectorPlaceholder.classList.remove("hidden");
        els.selectedPill.classList.add("hidden");
        fetchBooks();
    } catch (err) {
        showToast(err.message, "error");
    }
};

els.lookupBtn.onclick = async () => {
    const isbn = els.formIsbn.value.trim();
    if (!isbn) {
        showToast("Digite um ISBN primeiro.", "info");
        return;
    }
    
    els.lookupBtn.innerHTML = '<i class="loader-spinner" style="width:14px; height:14px; border-width:1px"></i>';
    try {
        const data = await lookupISBN(isbn);
        if (data.title) els.formTitleInput.value = data.title;
        if (data.author) els.formAuthorInput.value = data.author;
        if (data.year) els.formYearInput.value = data.year;
        if (data.description) els.formDescInput.value = data.description;
        showToast("Dados recuperados via ISBN.");
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        els.lookupBtn.innerHTML = '<i data-lucide="zap"></i>';
        lucide.createIcons();
    }
};

// Start
fetchBooks();
lucide.createIcons();
