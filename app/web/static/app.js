/**
 * Library Studio - Premium Frontend Logic
 * Async/Await, Clean Architecture, Reactive State
 */

const apiBase = document.body.dataset.apiBase || "/api/v1";
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

// Icons are progressive enhancement: the app keeps working if the CDN script fails.
const renderIcons = () => window.lucide?.createIcons();

const createIcon = (name) => {
    const icon = document.createElement("i");
    icon.dataset.lucide = name;
    return icon;
};

// Builds an element whose text is always set via textContent (never parsed as HTML).
const createTextElement = (tag, className, text) => {
    const el = document.createElement(tag);
    el.className = className;
    el.textContent = text;
    return el;
};

const showToast = (message, type = "success") => {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    const icon = type === "success" ? "check-circle" : (type === "error" ? "alert-circle" : "info");
    toast.append(createIcon(icon), createTextElement("span", "", message));

    els.toastContainer.appendChild(toast);
    renderIcons();

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        setTimeout(() => toast.remove(), 400);
    }, 4000);
};

const readError = async (response, fallback) => {
    if (response.status === 429) {
        const wait = parseInt(response.headers.get("Retry-After") || "", 10);
        return Number.isFinite(wait)
            ? `Muitas requisições. Tente novamente em ${wait}s.`
            : "Muitas requisições. Tente novamente em instantes.";
    }
    try {
        const body = await response.json();
        if (typeof body.detail === "string") return body.detail;
        if (Array.isArray(body.detail)) {
            return body.detail
                .map((item) => {
                    const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : "";
                    return field ? `${field}: ${item.msg}` : item.msg;
                })
                .join("; ");
        }
    } catch {
        // Non-JSON error body: use the generic message below.
    }
    return fallback;
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
        if (!response.ok) throw new Error(await readError(response, "Erro ao carregar acervo."));

        const data = await response.json();
        state.books = data;
        state.total = parseInt(response.headers.get("X-Total-Count") || data.length, 10);
        
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

    if (!response.ok) throw new Error(await readError(response, "Erro ao salvar livro."));
    return response.json();
};

const deleteBook = async (id) => {
    const response = await fetch(`${bookEndpoint}${id}`, { method: "DELETE" });
    if (!response.ok) throw new Error(await readError(response, "Erro ao excluir livro."));
};

const lookupISBN = async (isbn) => {
    const response = await fetch(`${apiBase}/books/lookup/${encodeURIComponent(isbn)}`);
    if (!response.ok) {
        throw new Error(await readError(response, "ISBN não encontrado ou falha na API externa."));
    }
    return response.json();
};

/**
 * RENDERING
 */
const renderBooks = () => {
    els.list.replaceChildren();
    els.resultCount.textContent = `${state.total} resultados`;

    state.books.forEach((book, index) => {
        const isActive = book.id === state.selectedId;
        const item = document.createElement("button");
        item.type = "button";
        item.className = `book-item ${isActive ? "active" : ""}`;
        if (isActive) item.setAttribute("aria-current", "true");
        item.style.animationDelay = `${index * 0.05}s`;

        const statusCfg = STATUS_META[book.status] || STATUS_META.available;

        const info = document.createElement("span");
        info.className = "book-main-info";
        info.append(
            createTextElement("span", "book-title", book.title),
            createTextElement("span", "book-author", book.author),
        );

        const statusDot = createTextElement("span", `status-dot ${statusCfg.class}`, "");
        statusDot.title = statusCfg.label;

        const meta = document.createElement("span");
        meta.className = "book-meta";
        meta.append(createTextElement("span", "book-year", book.year || "-"), statusDot);

        item.append(info, meta);
        item.addEventListener("click", () => selectBook(book));
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
    
    if (book.cover_url && /^https?:\/\//i.test(book.cover_url)) {
        els.detailCoverImg.alt = `Capa de ${book.title}`;
        els.detailCoverImg.src = book.cover_url;
        els.detailCoverImg.classList.remove("hidden");
        els.detailCoverFallback.classList.add("hidden");
    } else {
        els.detailCoverImg.classList.add("hidden");
        els.detailCoverFallback.classList.remove("hidden");
    }

    // Re-rendering replaces the focused row, so move focus to its replacement.
    const listHadFocus = els.list.contains(document.activeElement);
    renderBooks();
    if (listHadFocus) els.list.querySelector('[aria-current="true"]')?.focus();

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

const setButtonBusy = (button, busy) => {
    button.disabled = busy;
    button.setAttribute("aria-busy", String(busy));
};

const showCoverFallback = () => {
    els.detailCoverImg.classList.add("hidden");
    els.detailCoverFallback.classList.remove("hidden");
};

/**
 * EVENT LISTENERS
 */
els.detailCoverImg.addEventListener("error", showCoverFallback);

els.refreshBtn.onclick = () => fetchBooks();

els.seedBtn.onclick = async () => {
    const examples = [
        { title: "Clean Code", author: "Robert C. Martin", year: 2008, isbn: "0132350882", status: "available" },
        { title: "Pragmatic Programmer", author: "Andrew Hunt", year: 1999, isbn: "020161622X", status: "available" }
    ];
    setButtonBusy(els.seedBtn, true);
    try {
        for (const ex of examples) await createOrUpdateBook(ex);
        showToast("Exemplos criados!");
        fetchBooks();
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        setButtonBusy(els.seedBtn, false);
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
    
    setButtonBusy(els.submitBtn, true);
    try {
        const saved = await createOrUpdateBook(payload);
        showToast(payload.id ? "Registro atualizado!" : "Livro cadastrado!");
        exitEditMode();
        await fetchBooks();
        selectBook(saved);
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        setButtonBusy(els.submitBtn, false);
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
    
    setButtonBusy(els.lookupBtn, true);
    els.lookupBtn.replaceChildren(createTextElement("span", "loader-spinner loader-spinner-sm", ""));
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
        els.lookupBtn.replaceChildren(createIcon("zap"));
        renderIcons();
        setButtonBusy(els.lookupBtn, false);
    }
};

// Start
fetchBooks();
renderIcons();
