(function () {
  "use strict";

  const app = document.getElementById("library-app");
  if (!app) return;

  const lang = app.dataset.lang === "en" ? "en" : "fr";
  const locale = lang === "en" ? "en-CA" : "fr-CA";
  const sourceUrl = app.dataset.source;
  const pageSize = 24;

  const copy = {
    fr: {
      book: "livre",
      books: "livres",
      entry: "entrée",
      entries: "entrées",
      untitled: "Titre non renseigné",
      unknownAuthor: "Auteur non renseigné",
      unknownPublisher: "Éditeur non renseigné",
      unknownValue: "Non renseigné",
      author: "Auteur",
      publisher: "Éditeur",
      sourceRecords: "Notices CLZ regroupées",
      year: "Année",
      isbn: "ISBN",
      date: "Date de publication",
      coverAlt: (title) => `Couverture de ${title}`,
      openLibrary: "Voir cette édition sur Open Library",
      coverSource: (provider) => `Voir la couverture sur ${provider}`,
      chartDecades: "Répartition des livres par décennie",
      chartPublishers: "Classement des éditeurs les plus présents",
      rarityAge: (count) => `${count} ans`,
      rarityPreIsbn: "Avant l’ISBN",
      rarityCoverFound: "Couverture retrouvée",
      rarityCoverMissing: "Couverture non retrouvée",
      more: (count) => `Afficher ${count} ${count === 1 ? "livre" : "livres"} de plus`,
      searchPlaceholder: (count) => `Rechercher dans ${formatNumber(count)} livres`,
      result: (count) => `${formatNumber(count)} ${count === 1 ? "livre" : "livres"}`,
      decadeOption: (decade) => `Années ${decade}`,
      openBook: (title) => `Ouvrir la fiche de ${title}`
    },
    en: {
      book: "book",
      books: "books",
      entry: "entry",
      entries: "entries",
      untitled: "Title not recorded",
      unknownAuthor: "Author not recorded",
      unknownPublisher: "Publisher not recorded",
      unknownValue: "Not recorded",
      author: "Author",
      publisher: "Publisher",
      sourceRecords: "Grouped CLZ records",
      year: "Year",
      isbn: "ISBN",
      date: "Publication date",
      coverAlt: (title) => `Cover of ${title}`,
      openLibrary: "View this edition on Open Library",
      coverSource: (provider) => `View the cover on ${provider}`,
      chartDecades: "Distribution of books by decade",
      chartPublishers: "Ranking of the most represented publishers",
      rarityAge: (count) => `${count} years old`,
      rarityPreIsbn: "Predates ISBN",
      rarityCoverFound: "Cover located",
      rarityCoverMissing: "Cover not located",
      more: (count) => `Show ${count} more ${count === 1 ? "book" : "books"}`,
      searchPlaceholder: (count) => `Search ${formatNumber(count)} books`,
      result: (count) => `${formatNumber(count)} ${count === 1 ? "book" : "books"}`,
      decadeOption: (decade) => `${decade}s`,
      openBook: (title) => `Open details for ${title}`
    }
  }[lang];

  const colors = [
    { bg: "#082f43", accent: "#d5a53f", text: "#ffffff" },
    { bg: "#0b6570", accent: "#e4bd55", text: "#ffffff" },
    { bg: "#b8202f", accent: "#f1c75b", text: "#ffffff" },
    { bg: "#f1eee7", accent: "#b8202f", text: "#102f3f" },
    { bg: "#b7791f", accent: "#fff1bf", text: "#ffffff" },
    { bg: "#102f3f", accent: "#42b7c5", text: "#ffffff" }
  ];

  const state = {
    records: [],
    query: "",
    decade: "",
    publisher: "",
    sort: "catalogue",
    visible: pageSize,
    rarityReferenceYear: new Date().getFullYear()
  };

  const elements = {
    search: document.getElementById("library-search"),
    decade: document.getElementById("library-decade"),
    publisher: document.getElementById("library-publisher"),
    sort: document.getElementById("library-sort"),
    reset: document.getElementById("library-reset"),
    count: document.getElementById("library-result-count"),
    grid: document.getElementById("library-book-grid"),
    empty: document.getElementById("library-empty"),
    loadMore: document.getElementById("library-load-more"),
    explore: document.getElementById("library-explore"),
    random: document.getElementById("library-random"),
    shelf: document.getElementById("library-hero-shelf"),
    decadeChart: document.getElementById("library-decade-chart"),
    publisherChart: document.getElementById("library-publisher-chart"),
    rarityGrid: document.getElementById("library-rarity-grid"),
    dialog: document.getElementById("library-dialog"),
    dialogContent: document.getElementById("library-dialog-content"),
    dialogClose: document.getElementById("library-dialog-close"),
    error: document.getElementById("library-error")
  };

  function formatNumber(value) {
    return new Intl.NumberFormat(locale).format(value);
  }

  function normalize(value) {
    return String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase(locale)
      .trim();
  }

  function publisherKey(value) {
    return String(value || "").toLocaleLowerCase(locale).trim();
  }

  function publisherFor(record) {
    return record.publisher_normalized || record.publisher || "";
  }

  function authorFor(record) {
    return record.author_normalized || record.author || copy.unknownAuthor;
  }

  function numericYear(record) {
    const value = String(record.publication_year || "").trim();
    return /^(18|19|20)\d{2}$/.test(value) ? Number(value) : null;
  }

  function hashString(value) {
    let hash = 2166136261;
    for (let i = 0; i < value.length; i += 1) {
      hash ^= value.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return Math.abs(hash >>> 0);
  }

  function paletteFor(record) {
    return colors[hashString(`${record.title}|${authorFor(record)}|${record.id}`) % colors.length];
  }

  function setCoverVariables(element, record) {
    const palette = paletteFor(record);
    element.style.setProperty("--cover-bg", palette.bg);
    element.style.setProperty("--cover-accent", palette.accent);
    element.style.setProperty("--cover-text", palette.text);
    element.classList.add(`pattern-${hashString(record.id) % 6}`);
  }

  function titleFor(record) {
    return record.title || copy.untitled;
  }

  function coverImageFor(record, size = "M") {
    const sizeKey = { S: "small", M: "medium", L: "large" }[size] || "medium";
    return record.cover?.images?.[sizeKey] || record.openlibrary?.cover?.[sizeKey] || "";
  }

  function canonicalPublisher(values) {
    return values[0] || "";
  }

  function publisherGroups(records) {
    const groups = new Map();
    records.forEach((record) => {
      const publisher = publisherFor(record);
      if (!publisher) return;
      const key = publisherKey(publisher);
      if (!groups.has(key)) groups.set(key, { key, values: [], count: 0 });
      const group = groups.get(key);
      group.count += 1;
      if (!group.values.includes(publisher)) group.values.push(publisher);
    });
    return Array.from(groups.values()).map((group) => ({
      ...group,
      label: canonicalPublisher(group.values)
    }));
  }

  function coverElement(record, className = "book-cover", imageSize = "M") {
    const cover = document.createElement("div");
    cover.className = className;
    setCoverVariables(cover, record);

    const title = document.createElement("span");
    title.className = "book-cover-title";
    title.textContent = titleFor(record);

    const author = document.createElement("span");
    author.className = "book-cover-author";
    author.textContent = authorFor(record);

    cover.append(title, author);

    const imageUrl = coverImageFor(record, imageSize);
    if (imageUrl) {
      const image = document.createElement("img");
      image.className = "book-cover-image";
      image.alt = copy.coverAlt(titleFor(record));
      image.loading = "lazy";
      image.decoding = "async";
      image.referrerPolicy = "no-referrer";
      image.addEventListener("load", () => {
        if (image.naturalWidth > 1 && image.naturalHeight > 1) {
          cover.classList.add("has-cover-image");
        } else {
          image.remove();
        }
      });
      image.addEventListener("error", () => image.remove());
      image.src = imageUrl;
      cover.append(image);
    }

    return cover;
  }

  function updateMetrics(records) {
    const years = records.map(numericYear).filter((year) => year !== null).sort((a, b) => a - b);
    const publisherLabels = new Set(records.map(publisherFor).filter(Boolean));
    const median = years.length % 2
      ? years[(years.length - 1) / 2]
      : Math.round((years[years.length / 2 - 1] + years[years.length / 2]) / 2);
    const range = `${Math.min(...years)}-${Math.max(...years)}`;
    const missingIsbn = records.filter((record) => !record.isbn).length;
    const pre1970MissingIsbn = records.filter((record) => record.isbn_status === "missing_pre_1970").length;
    const reviewIsbn = records.filter((record) =>
      ["missing_1970_or_later", "missing_unknown_year", "invalid"].includes(record.isbn_status)
    ).length;
    const coverCount = records.filter((record) => Boolean(coverImageFor(record))).length;
    const coverRate = records.length ? Math.round(1000 * coverCount / records.length) / 10 : 0;
    const sourceRecordCount = records.reduce((total, record) => total + Number(record.source_record_count || 1), 0);

    document.querySelectorAll("[data-total-books]").forEach((node) => {
      node.textContent = formatNumber(records.length);
    });
    document.querySelectorAll("[data-total-source-records]").forEach((node) => {
      node.textContent = formatNumber(sourceRecordCount);
    });
    document.querySelectorAll("[data-year-range]").forEach((node) => {
      node.textContent = range;
    });
    document.querySelectorAll("[data-publisher-count]").forEach((node) => {
      node.textContent = formatNumber(publisherLabels.size);
    });
    document.querySelectorAll("[data-median-year]").forEach((node) => {
      node.textContent = median;
    });
    document.querySelectorAll("[data-known-year-count]").forEach((node) => {
      node.textContent = formatNumber(years.length);
    });
    document.querySelectorAll("[data-missing-isbn-count]").forEach((node) => {
      node.textContent = formatNumber(missingIsbn);
    });
    document.querySelectorAll("[data-pre1970-missing-isbn-count]").forEach((node) => {
      node.textContent = formatNumber(pre1970MissingIsbn);
    });
    document.querySelectorAll("[data-review-isbn-count]").forEach((node) => {
      node.textContent = formatNumber(reviewIsbn);
    });
    document.querySelectorAll("[data-cover-count]").forEach((node) => {
      node.textContent = formatNumber(coverCount);
    });
    document.querySelectorAll("[data-cover-rate]").forEach((node) => {
      node.textContent = new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(coverRate);
    });

    elements.search.placeholder = copy.searchPlaceholder(records.length);
  }

  function renderShelf(records) {
    const wanted = [
      "Proofs from THE BOOK",
      "Complex Analysis",
      "All of Statistics A Concise Course in Statistical Inference",
      "Machine Learning, Animated",
      "Le livre des nombres",
      "Astronomical Algorithms",
      "Visual Complex Analysis",
      "Introduction to Statistical Inference",
      "Probability Theory A Concise Course",
      "Concrete Abstract Algebra"
    ];
    const selected = [];
    wanted.forEach((title) => {
      const record = records.find((item) => item.title === title || item.title.startsWith(title));
      if (record && !selected.includes(record)) selected.push(record);
    });

    const rows = [selected.slice(0, 6), selected.slice(6, 10)];
    elements.shelf.replaceChildren();
    rows.forEach((rowRecords, rowIndex) => {
      const row = document.createElement("div");
      row.className = "library-shelf-row";
      rowRecords.forEach((record, index) => {
        const spine = document.createElement("button");
        const palette = paletteFor(record);
        const hash = hashString(record.id);
        spine.className = "library-spine";
        spine.type = "button";
        spine.setAttribute("aria-label", copy.openBook(titleFor(record)));
        spine.style.setProperty("--cover-bg", palette.bg);
        spine.style.setProperty("--cover-accent", palette.accent);
        spine.style.setProperty("--cover-text", palette.text);
        spine.style.setProperty("--spine-height", `${rowIndex === 0 ? 250 + (hash % 48) : 205 + (hash % 42)}px`);
        spine.style.setProperty("--spine-width", `${76 + (hash % 23)}px`);
        spine.style.setProperty("--spine-width-tablet", `${63 + (hash % 17)}px`);

        const title = document.createElement("span");
        title.className = "library-spine-title";
        title.textContent = titleFor(record);

        const author = document.createElement("span");
        author.className = "library-spine-author";
        author.textContent = authorFor(record).replace(/\s*\|\s*/g, " · ");

        spine.append(title, author);
        spine.addEventListener("click", () => openDialog(record));
        row.append(spine);
      });
      elements.shelf.append(row);
    });
  }

  function renderDecadeChart(records) {
    const counts = new Map();
    records.forEach((record) => {
      const year = numericYear(record);
      if (year === null) return;
      const decade = Math.floor(year / 10) * 10;
      counts.set(decade, (counts.get(decade) || 0) + 1);
    });
    const values = Array.from(counts.entries()).sort((a, b) => a[0] - b[0]);
    const max = Math.max(...values.map(([, count]) => count));
    elements.decadeChart.replaceChildren();
    elements.decadeChart.style.setProperty("--decade-count", values.length);
    elements.decadeChart.setAttribute("role", "img");
    elements.decadeChart.setAttribute("aria-label", `${copy.chartDecades}: ${values.map(([decade, count]) => `${decade}, ${count}`).join("; ")}`);

    values.forEach(([decade, count], index) => {
      const palette = colors[index % colors.length];
      const item = document.createElement("div");
      item.className = "library-decade-item";

      const countLabel = document.createElement("span");
      countLabel.className = "library-decade-value";
      countLabel.textContent = count;

      const bar = document.createElement("div");
      bar.className = "library-decade-bar";
      bar.style.height = `${Math.max(2, (count / max) * 78)}%`;
      bar.style.setProperty("--bar-color", palette.bg);
      bar.style.setProperty("--bar-accent", palette.accent);

      const label = document.createElement("span");
      label.className = "library-decade-label";
      label.textContent = decade;

      item.append(countLabel, bar, label);
      elements.decadeChart.append(item);
    });
  }

  function renderPublisherChart(records) {
    const groups = publisherGroups(records).sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, locale));
    const top = groups.slice(0, 6);
    const max = top[0].count;
    elements.publisherChart.replaceChildren();
    elements.publisherChart.setAttribute("role", "img");
    elements.publisherChart.setAttribute("aria-label", `${copy.chartPublishers}: ${top.map((group) => `${group.label}, ${group.count}`).join("; ")}`);

    top.forEach((group, index) => {
      const palette = colors[index % colors.length];
      const row = document.createElement("div");
      row.className = "library-publisher-row";

      const label = document.createElement("span");
      label.className = "library-publisher-label";
      label.textContent = group.label;

      const track = document.createElement("div");
      track.className = "library-publisher-track";
      const bar = document.createElement("div");
      bar.className = "library-publisher-bar";
      bar.style.width = `${(group.count / max) * 100}%`;
      bar.style.setProperty("--bar-color", palette.bg);
      bar.style.setProperty("--bar-accent", palette.accent);
      track.append(bar);

      const value = document.createElement("span");
      value.className = "library-publisher-value";
      value.textContent = group.count;

      row.append(label, track, value);
      elements.publisherChart.append(row);
    });
  }

  function rarityCandidates(records) {
    return records
      .filter((record) => {
        const year = numericYear(record);
        return year !== null
          && year < 1970
          && record.isbn_status === "missing_pre_1970"
          && Boolean(record.title && (record.author_normalized || record.author) && publisherFor(record));
      })
      .slice()
      .sort((a, b) => numericYear(a) - numericYear(b) || a._index - b._index);
  }

  function renderRarity(records) {
    if (!elements.rarityGrid) return;

    const candidates = rarityCandidates(records);
    const selected = candidates.slice(0, 5);
    const cutoffYear = selected.length ? numericYear(selected[selected.length - 1]) : null;
    const excludedOlder = cutoffYear === null
      ? 0
      : records.filter((record) => {
          const year = numericYear(record);
          return year !== null
            && year < cutoffYear
            && record.isbn_status === "missing_pre_1970"
            && !candidates.includes(record);
        }).length;

    document.querySelectorAll("[data-rarity-excluded]").forEach((node) => {
      node.textContent = formatNumber(excludedOlder);
    });

    elements.rarityGrid.replaceChildren(...selected.map((record, index) => {
      const year = numericYear(record);
      const age = Math.max(0, state.rarityReferenceYear - year);
      const card = document.createElement("button");
      card.className = "library-rarity-card";
      card.type = "button";
      card.setAttribute("aria-label", copy.openBook(titleFor(record)));

      const rank = document.createElement("span");
      rank.className = "library-rarity-rank";
      rank.textContent = String(index + 1).padStart(2, "0");

      const cover = coverElement(record, "book-cover library-rarity-cover", "M");
      const meta = document.createElement("div");
      meta.className = "library-rarity-meta";

      const yearLabel = document.createElement("p");
      yearLabel.className = "library-rarity-year";
      yearLabel.textContent = String(year);

      const title = document.createElement("h3");
      title.textContent = titleFor(record);

      const author = document.createElement("p");
      author.className = "library-rarity-author";
      author.textContent = authorFor(record).replace(/\s*\|\s*/g, " · ");

      const publisher = document.createElement("p");
      publisher.className = "library-rarity-publisher";
      publisher.textContent = publisherFor(record);

      const signals = document.createElement("div");
      signals.className = "library-rarity-signals";
      const coverSignal = coverImageFor(record)
        ? copy.rarityCoverFound
        : copy.rarityCoverMissing;
      [copy.rarityAge(age), copy.rarityPreIsbn, coverSignal].forEach((label) => {
        const signal = document.createElement("span");
        signal.textContent = label;
        signals.append(signal);
      });

      meta.append(yearLabel, title, author, publisher, signals);
      card.append(rank, cover, meta);
      card.addEventListener("click", () => openDialog(record));
      return card;
    }));
  }

  function populateFilters(records) {
    const decades = Array.from(new Set(records.map(numericYear).filter((year) => year !== null).map((year) => Math.floor(year / 10) * 10))).sort((a, b) => a - b);
    decades.forEach((decade) => {
      const option = document.createElement("option");
      option.value = decade;
      option.textContent = copy.decadeOption(decade);
      elements.decade.append(option);
    });

    publisherGroups(records)
      .sort((a, b) => a.label.localeCompare(b.label, locale, { sensitivity: "base" }))
      .forEach((publisher) => {
        const option = document.createElement("option");
        option.value = publisher.key;
        option.textContent = publisher.label;
        elements.publisher.append(option);
      });
  }

  function filteredRecords() {
    const query = normalize(state.query);
    let records = state.records.filter((record) => {
      const year = numericYear(record);
      const matchesQuery = !query || normalize([record.title, record.author, authorFor(record), record.isbn, record.publisher, publisherFor(record)].join(" ")).includes(query);
      const matchesDecade = !state.decade || (year !== null && Math.floor(year / 10) * 10 === Number(state.decade));
      const matchesPublisher = !state.publisher || publisherKey(publisherFor(record)) === state.publisher;
      return matchesQuery && matchesDecade && matchesPublisher;
    });

    const compareText = (field) => (a, b) => normalize(a[field]).localeCompare(normalize(b[field]), locale, { sensitivity: "base" }) || a._index - b._index;
    if (state.sort === "title") records = records.slice().sort(compareText("title"));
    if (state.sort === "author") records = records.slice().sort((a, b) => normalize(authorFor(a)).localeCompare(normalize(authorFor(b)), locale, { sensitivity: "base" }) || a._index - b._index);
    if (state.sort === "newest") records = records.slice().sort((a, b) => (numericYear(b) || -Infinity) - (numericYear(a) || -Infinity) || a._index - b._index);
    if (state.sort === "oldest") records = records.slice().sort((a, b) => (numericYear(a) || Infinity) - (numericYear(b) || Infinity) || a._index - b._index);
    return records;
  }

  function bookCard(record) {
    const button = document.createElement("button");
    button.className = "book-card";
    button.type = "button";
    button.setAttribute("aria-label", copy.openBook(titleFor(record)));

    const cover = coverElement(record);
    const meta = document.createElement("div");
    meta.className = "book-card-meta";

    const title = document.createElement("p");
    title.className = "book-card-title";
    title.textContent = titleFor(record);

    const author = document.createElement("p");
    author.className = "book-card-author";
    author.textContent = authorFor(record).replace(/\s*\|\s*/g, " · ");

    const year = document.createElement("p");
    year.className = "book-card-year";
    year.textContent = record.publication_year || copy.unknownValue;

    meta.append(title, author, year);
    button.append(cover, meta);
    button.addEventListener("click", () => openDialog(record));
    return button;
  }

  function renderCatalogue() {
    const records = filteredRecords();
    const visible = records.slice(0, state.visible);
    elements.grid.replaceChildren(...visible.map(bookCard));
    elements.count.textContent = copy.result(records.length);
    elements.empty.hidden = records.length !== 0;
    elements.grid.hidden = records.length === 0;

    const remaining = Math.max(0, records.length - visible.length);
    elements.loadMore.hidden = remaining === 0;
    if (remaining > 0) elements.loadMore.textContent = copy.more(Math.min(pageSize, remaining));
  }

  function detailRow(label, value) {
    const row = document.createElement("div");
    row.className = "library-dialog-row";
    const term = document.createElement("dt");
    term.textContent = label;
    const definition = document.createElement("dd");
    definition.textContent = value || copy.unknownValue;
    row.append(term, definition);
    return row;
  }

  function openDialog(record) {
    elements.dialogContent.replaceChildren();
    const head = document.createElement("div");
    head.className = "library-dialog-head";
    const cover = coverElement(record, "book-cover", "L");
    const titleWrap = document.createElement("div");
    titleWrap.className = "library-dialog-title-wrap";
    const title = document.createElement("h2");
    title.id = "library-dialog-title";
    title.textContent = titleFor(record);
    const author = document.createElement("p");
    author.className = "library-dialog-author";
    author.textContent = authorFor(record).replace(/\s*\|\s*/g, " · ");
    titleWrap.append(title, author);
    head.append(cover, titleWrap);

    const details = document.createElement("dl");
    details.className = "library-dialog-details";
    const detailRows = [
      detailRow(copy.author, authorFor(record)),
      detailRow(copy.publisher, publisherFor(record)),
      detailRow(copy.year, record.publication_year),
      detailRow(copy.date, record.publication_date),
      detailRow(copy.isbn, record.isbn)
    ];
    if (Number(record.source_record_count || 1) > 1) {
      detailRows.push(detailRow(copy.sourceRecords, String(record.source_record_count)));
    }
    details.append(...detailRows);
    elements.dialogContent.append(head, details);

    const coverSourceUrl = record.cover?.source_url || "";
    const verifiedEditionUrl = record.openlibrary?.url || "";
    const externalUrl = coverSourceUrl || verifiedEditionUrl;
    if (externalUrl) {
      const externalLink = document.createElement("a");
      externalLink.className = "library-dialog-external";
      externalLink.href = externalUrl;
      externalLink.target = "_blank";
      externalLink.rel = "noopener noreferrer";
      const linkLabel = coverSourceUrl
        ? copy.coverSource(record.cover?.provider || "Open Library")
        : copy.openLibrary;
      externalLink.innerHTML = `<i class="bi bi-box-arrow-up-right" aria-hidden="true"></i><span>${linkLabel}</span>`;
      elements.dialogContent.append(externalLink);
    }

    if (typeof elements.dialog.showModal === "function") {
      elements.dialog.showModal();
    } else {
      elements.dialog.setAttribute("open", "");
    }
  }

  function resetFilters() {
    state.query = "";
    state.decade = "";
    state.publisher = "";
    state.sort = "catalogue";
    state.visible = pageSize;
    elements.search.value = "";
    elements.decade.value = "";
    elements.publisher.value = "";
    elements.sort.value = "catalogue";
    renderCatalogue();
  }

  function bindEvents() {
    elements.search.addEventListener("input", (event) => {
      state.query = event.target.value;
      state.visible = pageSize;
      renderCatalogue();
    });
    elements.decade.addEventListener("change", (event) => {
      state.decade = event.target.value;
      state.visible = pageSize;
      renderCatalogue();
    });
    elements.publisher.addEventListener("change", (event) => {
      state.publisher = event.target.value;
      state.visible = pageSize;
      renderCatalogue();
    });
    elements.sort.addEventListener("change", (event) => {
      state.sort = event.target.value;
      state.visible = pageSize;
      renderCatalogue();
    });
    elements.reset.addEventListener("click", resetFilters);
    elements.loadMore.addEventListener("click", () => {
      state.visible += pageSize;
      renderCatalogue();
    });
    elements.explore.addEventListener("click", () => {
      document.getElementById("catalogue-title").scrollIntoView({ behavior: "smooth", block: "start" });
      window.setTimeout(() => elements.search.focus({ preventScroll: true }), 500);
    });
    elements.random.addEventListener("click", () => {
      const record = state.records[Math.floor(Math.random() * state.records.length)];
      openDialog(record);
    });
    elements.dialogClose.addEventListener("click", () => elements.dialog.close());
    elements.dialog.addEventListener("click", (event) => {
      if (event.target === elements.dialog) elements.dialog.close();
    });
  }

  async function init() {
    try {
      const response = await fetch(sourceUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      if (!payload || !Array.isArray(payload.records)) throw new Error("Invalid catalogue payload");

      state.records = payload.records.map((record, index) => ({ ...record, _index: index }));
      state.rarityReferenceYear = Number(String(payload.curation?.curated_on || "").slice(0, 4)) || state.rarityReferenceYear;
      updateMetrics(state.records);
      renderShelf(state.records);
      renderDecadeChart(state.records);
      renderPublisherChart(state.records);
      renderRarity(state.records);
      populateFilters(state.records);
      renderCatalogue();
      bindEvents();
    } catch (error) {
      elements.error.hidden = false;
      console.error("Library catalogue loading failed", error);
    }
  }

  init();
})();
