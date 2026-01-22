const apiBase = window.APP_CONFIG?.apiBase || "/api/v1";
const bookEndpoint = `${apiBase}/books/`;

const state = {
  books: [],
  selectedId: null,
  total: 0,
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

const els = {
  list: document.getElementById("book-list"),
  listState: document.getElementById("list-state"),
  resultCount: document.getElementById("result-count"),
  searchInput: document.getElementById("search-input"),
  authorInput: document.getElementById("author-input"),
  yearMin: document.getElementById("year-min"),
  yearMax: document.getElementById("year-max"),
  sortSelect: document.getElementById("sort-select"),
  orderSelect: document.getElementById("order-select"),
  limitSelect: document.getElementById("limit-select"),
  refreshBtn: document.getElementById("refresh-btn"),
  seedBtn: document.getElementById("seed-btn"),
  clearBtn: document.getElementById("clear-btn"),
  statTotal: document.getElementById("stat-total"),
  statLatest: document.getElementById("stat-latest"),
  statIsbn: document.getElementById("stat-isbn"),
  selectedPill: document.getElementById("selected-pill"),
  inspectorEmpty: document.querySelector(".inspector-empty"),
  inspectorContent: document.querySelector(".inspector-content"),
  detailTitle: document.getElementById("detail-title"),
  detailAuthor: document.getElementById("detail-author"),
  detailYear: document.getElementById("detail-year"),
  detailIsbn: document.getElementById("detail-isbn"),
  detailId: document.getElementById("detail-id"),
  deleteBtn: document.getElementById("delete-btn"),
  createForm: document.getElementById("create-form"),
  editForm: document.getElementById("edit-form"),
  toast: document.getElementById("toast"),
};

const editFields = {
  title: els.editForm.querySelector('input[name="title"]'),
  author: els.editForm.querySelector('input[name="author"]'),
  year: els.editForm.querySelector('input[name="year"]'),
  isbn: els.editForm.querySelector('input[name="isbn"]'),
};

const debounce = (fn, wait = 400) => {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
};

const showToast = (message, tone = "info") => {
  els.toast.textContent = message;
  els.toast.classList.remove("hidden");
  els.toast.style.background = tone === "error" ? "#d1495b" : "#1a1c1f";
  setTimeout(() => els.toast.classList.add("hidden"), 2200);
};

const buildQuery = () => {
  const params = new URLSearchParams();
  if (state.filters.q.trim().length >= 2) params.set("q", state.filters.q.trim());
  if (state.filters.author.trim()) params.set("author", state.filters.author.trim());
  if (state.filters.yearMin) params.set("year_min", state.filters.yearMin);
  if (state.filters.yearMax) params.set("year_max", state.filters.yearMax);
  params.set("limit", state.filters.limit);
  params.set("sort", state.filters.sort);
  params.set("order", state.filters.order);
  return params.toString();
};

const fetchBooks = async () => {
  els.listState.textContent = "Carregando...";
  if (state.filters.yearMin && state.filters.yearMax) {
    const minYear = Number(state.filters.yearMin);
    const maxYear = Number(state.filters.yearMax);
    if (minYear > maxYear) {
      els.listState.textContent = "Ajuste o intervalo de anos.";
      showToast("Ano minimo maior que ano maximo.", "error");
      return;
    }
  }
  try {
    const response = await fetch(`${bookEndpoint}?${buildQuery()}`);
    if (!response.ok) throw new Error("Erro ao buscar livros");
    const data = await response.json();
    state.total = Number(response.headers.get("X-Total-Count") || data.length);
    state.books = data;
    renderBooks();
    renderStats();
  } catch (err) {
    els.listState.textContent = "Nao foi possivel carregar.";
    showToast(err.message, "error");
  }
};

const renderBooks = () => {
  els.list.innerHTML = "";
  els.listState.textContent = state.books.length ? "" : "Nenhum resultado encontrado.";
  els.resultCount.textContent = `${state.total} resultados`;

  state.books.forEach((book, index) => {
    const card = document.createElement("div");
    card.className = "book-card";
    if (book.id === state.selectedId) card.classList.add("active");
    card.style.animationDelay = `${index * 0.03}s`;
    card.innerHTML = `
      <h4>${book.title}</h4>
      <p class="muted">${book.author}</p>
      <div class="detail-meta">
        <span>${book.year || "Ano nao informado"}</span>
        <span>${book.isbn || "ISBN livre"}</span>
      </div>
    `;
    card.addEventListener("click", () => selectBook(book));
    els.list.appendChild(card);
  });
};

const renderStats = () => {
  els.statTotal.textContent = state.total;
  const years = state.books.map((book) => book.year).filter(Boolean);
  els.statLatest.textContent = years.length ? Math.max(...years) : "-";
  const isbnCount = state.books.filter((book) => book.isbn).length;
  els.statIsbn.textContent = isbnCount;
};

const selectBook = (book) => {
  state.selectedId = book.id;
  els.selectedPill.textContent = `Selecionado #${book.id}`;
  els.inspectorEmpty.classList.add("hidden");
  els.inspectorContent.classList.remove("hidden");
  els.detailTitle.textContent = book.title;
  els.detailAuthor.textContent = book.author;
  els.detailYear.textContent = book.year ? `Ano ${book.year}` : "Ano nao informado";
  els.detailIsbn.textContent = book.isbn ? `ISBN ${book.isbn}` : "Sem ISBN";
  els.detailId.textContent = `ID ${book.id}`;
  els.editForm.dataset.id = book.id;
  editFields.title.value = book.title;
  editFields.author.value = book.author;
  editFields.year.value = book.year || "";
  editFields.isbn.value = book.isbn || "";
  renderBooks();
};

const clearSelection = () => {
  state.selectedId = null;
  els.selectedPill.textContent = "Nenhum selecionado";
  els.inspectorEmpty.classList.remove("hidden");
  els.inspectorContent.classList.add("hidden");
  els.editForm.dataset.id = "";
  els.editForm.reset();
  renderBooks();
};

const createBook = async (payload) => {
  const response = await fetch(bookEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Falha ao criar livro");
  }
  return response.json();
};

const updateBook = async (bookId, payload) => {
  const response = await fetch(`${bookEndpoint}${bookId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Falha ao atualizar livro");
  }
  return response.json();
};

const deleteBook = async (bookId) => {
  const response = await fetch(`${bookEndpoint}${bookId}`, { method: "DELETE" });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Falha ao remover livro");
  }
};

const seedExample = async () => {
  const example = {
    title: "Cosmos e o Codigo",
    author: "Lia Matins",
    year: 2026,
    isbn: `LS-${Math.floor(Math.random() * 9000 + 1000)}`,
  };
  await createBook(example);
  await fetchBooks();
  showToast("Livro exemplo criado.");
};

els.searchInput.addEventListener(
  "input",
  debounce((event) => {
    state.filters.q = event.target.value;
    fetchBooks();
  })
);

els.authorInput.addEventListener(
  "input",
  debounce((event) => {
    state.filters.author = event.target.value;
    fetchBooks();
  })
);

els.yearMin.addEventListener("change", (event) => {
  state.filters.yearMin = event.target.value;
  fetchBooks();
});

els.yearMax.addEventListener("change", (event) => {
  state.filters.yearMax = event.target.value;
  fetchBooks();
});

els.sortSelect.addEventListener("change", (event) => {
  state.filters.sort = event.target.value;
  fetchBooks();
});

els.orderSelect.addEventListener("change", (event) => {
  state.filters.order = event.target.value;
  fetchBooks();
});

els.limitSelect.addEventListener("change", (event) => {
  state.filters.limit = Number(event.target.value);
  fetchBooks();
});

els.refreshBtn.addEventListener("click", fetchBooks);
els.seedBtn.addEventListener("click", seedExample);
els.clearBtn.addEventListener("click", () => {
  state.filters = { ...state.filters, q: "", author: "", yearMin: "", yearMax: "" };
  els.searchInput.value = "";
  els.authorInput.value = "";
  els.yearMin.value = "";
  els.yearMax.value = "";
  fetchBooks();
});

els.createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(els.createForm);
  const payload = Object.fromEntries(formData.entries());
  if (payload.year === "") delete payload.year;
  if (payload.isbn === "") delete payload.isbn;
  payload.year = payload.year ? Number(payload.year) : undefined;
  try {
    await createBook(payload);
    els.createForm.reset();
    await fetchBooks();
    showToast("Livro criado com sucesso.");
  } catch (err) {
    showToast(err.message, "error");
  }
});

els.editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const bookId = els.editForm.dataset.id;
  if (!bookId) {
    showToast("Selecione um livro primeiro.", "error");
    return;
  }
  const formData = new FormData(els.editForm);
  const payload = Object.fromEntries(formData.entries());
  if (payload.year === "") delete payload.year;
  if (payload.isbn === "") delete payload.isbn;
  payload.year = payload.year ? Number(payload.year) : undefined;
  try {
    const updated = await updateBook(bookId, payload);
    await fetchBooks();
    selectBook(updated);
    showToast("Livro atualizado.");
  } catch (err) {
    showToast(err.message, "error");
  }
});

els.deleteBtn.addEventListener("click", async () => {
  const bookId = state.selectedId;
  if (!bookId) return;
  if (!confirm("Deseja remover este livro?")) return;
  try {
    await deleteBook(bookId);
    showToast("Livro removido.");
    clearSelection();
    await fetchBooks();
  } catch (err) {
    showToast(err.message, "error");
  }
});

fetchBooks();
