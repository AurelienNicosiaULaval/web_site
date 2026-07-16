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
      openBook: (title) => `Ouvrir la fiche de ${title}`,
      themeCount: (count) => `${formatNumber(count)} ${count === 1 ? "livre" : "livres"}`,
      fullCollection: "Collection complète",
      themeOverview: (themes, books) => `${formatNumber(books)} livres répartis dans ${formatNumber(themes)} territoires thématiques.`,
      themeSelection: "Quelques livres de ce territoire",
      wallForTheme: "Voir les couvertures de ce thème",
      timelineAll: (count, first, last) => `${formatNumber(count)} livres publiés de ${first} à ${last}`,
      timelineDecade: (count, decade) => `${formatNumber(count)} livres publiés dans les années ${decade}`,
      wallStatus: (shown, total) => `${formatNumber(shown)} couvertures affichées sur ${formatNumber(total)}`,
      networkOverview: "Vue d’ensemble",
      networkOverviewText: (themes, authors, publishers) => `${formatNumber(themes)} thèmes, ${formatNumber(authors)} auteurs et ${formatNumber(publishers)} éditeurs sont représentés dans cette vue condensée.`,
      networkTheme: "Thème",
      networkAuthor: "Auteur",
      networkPublisher: "Éditeur",
      networkBooks: (count) => `${formatNumber(count)} ${count === 1 ? "livre associé" : "livres associés"}`,
      networkConnections: "Principales connexions",
      networkSearchNone: "Aucun auteur ou éditeur ne correspond à cette recherche."
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
      openBook: (title) => `Open details for ${title}`,
      themeCount: (count) => `${formatNumber(count)} ${count === 1 ? "book" : "books"}`,
      fullCollection: "Full collection",
      themeOverview: (themes, books) => `${formatNumber(books)} books distributed across ${formatNumber(themes)} thematic territories.`,
      themeSelection: "A few books from this territory",
      wallForTheme: "View this theme’s covers",
      timelineAll: (count, first, last) => `${formatNumber(count)} books published from ${first} to ${last}`,
      timelineDecade: (count, decade) => `${formatNumber(count)} books published in the ${decade}s`,
      wallStatus: (shown, total) => `${formatNumber(shown)} covers shown out of ${formatNumber(total)}`,
      networkOverview: "Overview",
      networkOverviewText: (themes, authors, publishers) => `${formatNumber(themes)} themes, ${formatNumber(authors)} authors, and ${formatNumber(publishers)} publishers are represented in this condensed view.`,
      networkTheme: "Theme",
      networkAuthor: "Author",
      networkPublisher: "Publisher",
      networkBooks: (count) => `${formatNumber(count)} associated ${count === 1 ? "book" : "books"}`,
      networkConnections: "Main connections",
      networkSearchNone: "No author or publisher matches this search."
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
    rarityReferenceYear: new Date().getFullYear(),
    selectedTheme: "",
    timelineDecade: "",
    wallDecade: "",
    wallTheme: "",
    wallVisible: 32,
    wallSeed: 1,
    networkGraph: null,
    networkSelected: "",
    networkOverview: false
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
    themeMap: document.getElementById("library-theme-map"),
    themeDetail: document.getElementById("library-theme-detail"),
    themeReset: document.getElementById("library-theme-reset"),
    timelineChart: document.getElementById("library-timeline-chart"),
    timelineStatus: document.getElementById("library-timeline-status"),
    timelineBooks: document.getElementById("library-timeline-books"),
    timelineReset: document.getElementById("library-timeline-reset"),
    timelinePrev: document.getElementById("library-timeline-prev"),
    timelineNext: document.getElementById("library-timeline-next"),
    rarityGrid: document.getElementById("library-rarity-grid"),
    networkCanvas: document.getElementById("library-network-canvas"),
    networkDetail: document.getElementById("library-network-detail"),
    networkSearch: document.getElementById("library-network-search"),
    networkRecenter: document.getElementById("library-network-recenter"),
    networkAll: document.getElementById("library-network-all"),
    wallDecade: document.getElementById("library-wall-decade"),
    wallTheme: document.getElementById("library-wall-theme"),
    wallShuffle: document.getElementById("library-wall-shuffle"),
    wallStatus: document.getElementById("library-wall-status"),
    wallGrid: document.getElementById("library-cover-wall-grid"),
    wallMore: document.getElementById("library-wall-more"),
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

  const themeLabels = {
    "Mathématiques": lang === "en" ? "Mathematics" : "Mathématiques",
    "Statistique et probabilités": lang === "en" ? "Statistics and probability" : "Statistique et probabilités",
    "Informatique et science des données": lang === "en" ? "Computing and data science" : "Informatique et science des données",
    "Physique et sciences": lang === "en" ? "Physics and science" : "Physique et sciences",
    "Histoire et culture scientifique": lang === "en" ? "History and scientific culture" : "Histoire et culture scientifique",
    "Enseignement": lang === "en" ? "Teaching" : "Enseignement",
    "À classer": lang === "en" ? "To classify" : "À classer"
  };

  const themePalette = {
    "Mathématiques": "#0b7285",
    "Statistique et probabilités": "#102f3f",
    "Informatique et science des données": "#b7791f",
    "Physique et sciences": "#467b88",
    "Histoire et culture scientifique": "#8d6544",
    "Enseignement": "#6a7781",
    "À classer": "#a7afb4"
  };

  function themeFor(record) {
    return record.theme || "À classer";
  }

  function themeLabel(theme) {
    return themeLabels[theme] || theme;
  }

  function splitRecordAuthors(record) {
    return authorFor(record)
      .split(/\s*\|\s*/)
      .map((author) => author.trim())
      .filter((author) => author && author !== copy.unknownAuthor);
  }

  function themeGroups(records) {
    const groups = new Map();
    records.forEach((record) => {
      const theme = themeFor(record);
      if (!groups.has(theme)) groups.set(theme, []);
      groups.get(theme).push(record);
    });
    return Array.from(groups, ([theme, books]) => ({ theme, books, count: books.length }))
      .sort((a, b) => b.count - a.count || themeLabel(a.theme).localeCompare(themeLabel(b.theme), locale));
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

  function compactBookButton(record, className) {
    const button = document.createElement("button");
    button.className = className;
    button.type = "button";
    button.setAttribute("aria-label", copy.openBook(titleFor(record)));

    const cover = coverElement(record, "book-cover", "M");
    const meta = document.createElement("span");
    meta.className = "library-compact-book-meta";
    const title = document.createElement("strong");
    title.textContent = titleFor(record);
    const byline = document.createElement("span");
    byline.textContent = `${authorFor(record).replace(/\s*\|\s*/g, " · ")} · ${record.publication_year || copy.unknownValue}`;
    meta.append(title, byline);
    button.append(cover, meta);
    button.addEventListener("click", () => openDialog(record));
    return button;
  }

  function renderThemeAtlas(records) {
    if (!elements.themeMap || !elements.themeDetail) return;
    const groups = themeGroups(records);
    const total = records.length;
    elements.themeMap.replaceChildren();

    groups.forEach((group, index) => {
      const territory = document.createElement("button");
      territory.className = "library-theme-territory";
      territory.type = "button";
      territory.dataset.theme = group.theme;
      territory.setAttribute("aria-pressed", String(state.selectedTheme === group.theme));
      territory.setAttribute("aria-label", `${themeLabel(group.theme)}, ${copy.themeCount(group.count)}`);
      territory.style.setProperty("--theme-color", themePalette[group.theme] || colors[index % colors.length].bg);
      territory.style.setProperty("--theme-share", String(Math.max(1, Math.round(100 * group.count / total))));
      territory.style.setProperty("--theme-rank", String(index));

      const label = document.createElement("strong");
      label.textContent = themeLabel(group.theme);
      const count = document.createElement("span");
      count.textContent = copy.themeCount(group.count);
      territory.append(label, count);
      territory.addEventListener("click", () => {
        state.selectedTheme = group.theme;
        renderThemeAtlas(records);
      });
      elements.themeMap.append(territory);
    });

    elements.themeDetail.replaceChildren();
    if (!state.selectedTheme) {
      const title = document.createElement("h3");
      title.textContent = copy.fullCollection;
      const summary = document.createElement("p");
      summary.className = "library-theme-summary";
      summary.textContent = copy.themeOverview(groups.length, total);
      const list = document.createElement("ol");
      list.className = "library-theme-ranking";
      groups.forEach((group) => {
        const item = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        const label = document.createElement("span");
        label.textContent = themeLabel(group.theme);
        const count = document.createElement("strong");
        count.textContent = formatNumber(group.count);
        button.append(label, count);
        button.addEventListener("click", () => {
          state.selectedTheme = group.theme;
          renderThemeAtlas(records);
        });
        item.append(button);
        list.append(item);
      });
      elements.themeDetail.append(title, summary, list);
      return;
    }

    const group = groups.find((item) => item.theme === state.selectedTheme) || groups[0];
    const title = document.createElement("h3");
    title.textContent = themeLabel(group.theme);
    const summary = document.createElement("p");
    summary.className = "library-theme-summary";
    summary.textContent = copy.themeCount(group.count);
    const subhead = document.createElement("p");
    subhead.className = "library-detail-label";
    subhead.textContent = copy.themeSelection;
    const books = document.createElement("div");
    books.className = "library-theme-books";
    group.books
      .slice()
      .sort((a, b) => Number(Boolean(coverImageFor(b))) - Number(Boolean(coverImageFor(a))) || a._index - b._index)
      .slice(0, 3)
      .forEach((record) => books.append(compactBookButton(record, "library-theme-book")));
    const wallLink = document.createElement("button");
    wallLink.className = "library-detail-action";
    wallLink.type = "button";
    wallLink.textContent = copy.wallForTheme;
    wallLink.addEventListener("click", () => {
      state.wallTheme = group.theme;
      state.wallVisible = 32;
      if (elements.wallTheme) elements.wallTheme.value = group.theme;
      renderCoverWall(records);
      document.getElementById("cover-wall-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    elements.themeDetail.append(title, summary, subhead, books, wallLink);
  }

  function decadeGroups(records) {
    const groups = new Map();
    records.forEach((record) => {
      const year = numericYear(record);
      if (year === null) return;
      const decade = Math.floor(year / 10) * 10;
      if (!groups.has(decade)) groups.set(decade, []);
      groups.get(decade).push(record);
    });
    return Array.from(groups, ([decade, books]) => ({ decade, books, count: books.length }))
      .sort((a, b) => a.decade - b.decade);
  }

  function timelineBookSelection(records, limit = 5) {
    const covered = records.filter((record) => coverImageFor(record)).sort((a, b) => (numericYear(a) || 0) - (numericYear(b) || 0) || a._index - b._index);
    const pool = covered.length >= limit ? covered : records;
    if (pool.length <= limit) return pool;
    const selected = [];
    for (let index = 0; index < limit; index += 1) {
      const position = Math.round(index * (pool.length - 1) / (limit - 1));
      if (!selected.includes(pool[position])) selected.push(pool[position]);
    }
    return selected;
  }

  function renderTimeline(records) {
    if (!elements.timelineChart || !elements.timelineStatus || !elements.timelineBooks) return;
    const groups = decadeGroups(records);
    const max = Math.max(...groups.map((group) => group.count));
    const years = records.map(numericYear).filter((year) => year !== null);
    const selected = groups.find((group) => String(group.decade) === String(state.timelineDecade));

    elements.timelineChart.replaceChildren();
    groups.forEach((group) => {
      const button = document.createElement("button");
      button.className = "library-timeline-decade";
      button.type = "button";
      button.setAttribute("aria-pressed", String(Boolean(selected && selected.decade === group.decade)));
      button.setAttribute("aria-label", `${copy.decadeOption(group.decade)}, ${copy.themeCount(group.count)}`);
      button.style.setProperty("--timeline-height", `${Math.max(10, Math.round(100 * group.count / max))}%`);
      const count = document.createElement("strong");
      count.textContent = formatNumber(group.count);
      const bar = document.createElement("span");
      bar.className = "library-timeline-spine";
      const label = document.createElement("span");
      label.className = "library-timeline-decade-label";
      label.textContent = String(group.decade);
      button.append(count, bar, label);
      button.addEventListener("click", () => {
        state.timelineDecade = String(group.decade);
        renderTimeline(records);
        elements.timelineChart.querySelector('[aria-pressed="true"]')?.scrollIntoView({ block: "nearest", inline: "center" });
      });
      elements.timelineChart.append(button);
    });

    const activeRecords = selected ? selected.books : records;
    elements.timelineStatus.textContent = selected
      ? copy.timelineDecade(selected.count, selected.decade)
      : copy.timelineAll(records.length, Math.min(...years), Math.max(...years));
    elements.timelineBooks.replaceChildren(
      ...timelineBookSelection(activeRecords).map((record) => compactBookButton(record, "library-timeline-book"))
    );
    const selectedIndex = selected ? groups.indexOf(selected) : -1;
    elements.timelinePrev.disabled = selectedIndex <= 0;
    elements.timelineNext.disabled = selectedIndex < 0 || selectedIndex >= groups.length - 1;
  }

  function populateExplorationFilters(records) {
    const groups = decadeGroups(records);
    groups.forEach((group) => {
      const option = document.createElement("option");
      option.value = String(group.decade);
      option.textContent = copy.decadeOption(group.decade);
      elements.wallDecade?.append(option);
    });
    themeGroups(records).forEach((group) => {
      const option = document.createElement("option");
      option.value = group.theme;
      option.textContent = `${themeLabel(group.theme)} (${formatNumber(group.count)})`;
      elements.wallTheme?.append(option);
    });
  }

  function wallRecords(records) {
    return records
      .filter((record) => {
        const year = numericYear(record);
        return Boolean(coverImageFor(record))
          && (!state.wallDecade || (year !== null && Math.floor(year / 10) * 10 === Number(state.wallDecade)))
          && (!state.wallTheme || themeFor(record) === state.wallTheme);
      })
      .slice()
      .sort((a, b) => hashString(`${state.wallSeed}|${a.id}`) - hashString(`${state.wallSeed}|${b.id}`));
  }

  function renderCoverWall(records) {
    if (!elements.wallGrid || !elements.wallStatus) return;
    const filtered = wallRecords(records);
    const visible = filtered.slice(0, state.wallVisible);
    elements.wallGrid.replaceChildren(...visible.map((record) => {
      const button = document.createElement("button");
      button.className = "library-wall-cover";
      button.type = "button";
      button.setAttribute("aria-label", copy.openBook(titleFor(record)));
      const image = document.createElement("img");
      image.src = coverImageFor(record, "M");
      image.alt = copy.coverAlt(titleFor(record));
      image.loading = "lazy";
      image.decoding = "async";
      image.referrerPolicy = "no-referrer";
      const caption = document.createElement("span");
      caption.textContent = titleFor(record);
      button.append(image, caption);
      button.addEventListener("click", () => openDialog(record));
      return button;
    }));
    elements.wallStatus.textContent = copy.wallStatus(visible.length, filtered.length);
    const remaining = Math.max(0, filtered.length - visible.length);
    elements.wallMore.hidden = remaining === 0;
    if (remaining > 0) elements.wallMore.textContent = copy.more(Math.min(32, remaining));
  }

  function buildNetworkGraph(records) {
    const nodes = new Map();
    const edgeCounts = new Map();
    const nodeId = (type, label) => `${type}:${normalize(label)}`;
    const touchNode = (type, label) => {
      const id = nodeId(type, label);
      if (!nodes.has(id)) nodes.set(id, { id, type, label, count: 0 });
      nodes.get(id).count += 1;
      return id;
    };
    const touchEdge = (source, target) => {
      const id = `${source}|${target}`;
      edgeCounts.set(id, (edgeCounts.get(id) || 0) + 1);
    };

    records.forEach((record) => {
      const theme = themeFor(record);
      const themeId = touchNode("theme", theme);
      new Set(splitRecordAuthors(record)).forEach((author) => {
        const authorId = touchNode("author", author);
        touchEdge(themeId, authorId);
      });
      const publisher = publisherFor(record);
      if (publisher) {
        const publisherId = touchNode("publisher", publisher);
        touchEdge(themeId, publisherId);
      }
    });

    const edges = Array.from(edgeCounts, ([id, count]) => {
      const [source, target] = id.split("|");
      return { id, source, target, count };
    });
    return { nodes, edges };
  }

  function networkTypeLabel(type) {
    return {
      theme: copy.networkTheme,
      author: copy.networkAuthor,
      publisher: copy.networkPublisher
    }[type] || type;
  }

  function networkVisibleGraph(graph) {
    const allNodes = Array.from(graph.nodes.values());
    if (state.networkOverview) {
      const themes = allNodes.filter((node) => node.type === "theme");
      const authors = allNodes.filter((node) => node.type === "author")
        .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, locale)).slice(0, 8);
      const publishers = allNodes.filter((node) => node.type === "publisher")
        .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, locale)).slice(0, 8);
      const nodes = [...themes, ...authors, ...publishers];
      const ids = new Set(nodes.map((node) => node.id));
      const edges = graph.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target));
      return { nodes, edges };
    }

    const selected = graph.nodes.get(state.networkSelected) || allNodes.find((node) => node.type === "theme");
    state.networkSelected = selected?.id || "";
    const incident = graph.edges
      .filter((edge) => edge.source === state.networkSelected || edge.target === state.networkSelected)
      .sort((a, b) => b.count - a.count)
      .slice(0, window.matchMedia("(max-width: 700px)").matches ? 8 : 11);
    const ids = new Set([state.networkSelected]);
    incident.forEach((edge) => {
      ids.add(edge.source);
      ids.add(edge.target);
    });
    return {
      nodes: Array.from(ids).map((id) => graph.nodes.get(id)).filter(Boolean),
      edges: incident
    };
  }

  function networkPositions(nodes, width, height, overview) {
    const positions = new Map();
    const distribute = (items, x, top, bottom) => {
      items.forEach((node, index) => {
        const y = items.length === 1 ? (top + bottom) / 2 : top + index * (bottom - top) / (items.length - 1);
        positions.set(node.id, { x, y });
      });
    };

    if (overview) {
      distribute(nodes.filter((node) => node.type === "author"), width * 0.14, 48, height - 48);
      distribute(nodes.filter((node) => node.type === "theme"), width * 0.5, 45, height - 45);
      distribute(nodes.filter((node) => node.type === "publisher"), width * 0.86, 48, height - 48);
      return positions;
    }

    const selected = nodes.find((node) => node.id === state.networkSelected) || nodes[0];
    positions.set(selected.id, { x: width / 2, y: height / 2 });
    const neighbours = nodes.filter((node) => node.id !== selected.id);
    const radiusX = width * (width < 500 ? 0.37 : 0.39);
    const radiusY = height * 0.38;
    neighbours.forEach((node, index) => {
      const angle = -Math.PI / 2 + index * 2 * Math.PI / Math.max(1, neighbours.length);
      positions.set(node.id, {
        x: width / 2 + Math.cos(angle) * radiusX,
        y: height / 2 + Math.sin(angle) * radiusY
      });
    });
    return positions;
  }

  function renderNetworkDetail(graph, visible) {
    elements.networkDetail.replaceChildren();
    if (state.networkOverview) {
      const title = document.createElement("h3");
      title.textContent = copy.networkOverview;
      const counts = Object.fromEntries(["theme", "author", "publisher"].map((type) => [type, visible.nodes.filter((node) => node.type === type).length]));
      const text = document.createElement("p");
      text.className = "library-network-summary";
      text.textContent = copy.networkOverviewText(counts.theme, counts.author, counts.publisher);
      elements.networkDetail.append(title, text);
      return;
    }

    const node = graph.nodes.get(state.networkSelected);
    if (!node) return;
    const type = document.createElement("p");
    type.className = "library-detail-label";
    type.textContent = networkTypeLabel(node.type);
    const title = document.createElement("h3");
    title.textContent = node.type === "theme" ? themeLabel(node.label) : node.label;
    const count = document.createElement("p");
    count.className = "library-network-summary";
    count.textContent = copy.networkBooks(node.count);
    const subhead = document.createElement("p");
    subhead.className = "library-detail-label";
    subhead.textContent = copy.networkConnections;
    const list = document.createElement("div");
    list.className = "library-network-connections";
    graph.edges
      .filter((edge) => edge.source === node.id || edge.target === node.id)
      .sort((a, b) => b.count - a.count)
      .slice(0, 7)
      .forEach((edge) => {
        const neighbourId = edge.source === node.id ? edge.target : edge.source;
        const neighbour = graph.nodes.get(neighbourId);
        const button = document.createElement("button");
        button.type = "button";
        const label = document.createElement("span");
        label.textContent = neighbour.type === "theme" ? themeLabel(neighbour.label) : neighbour.label;
        const count = document.createElement("strong");
        count.textContent = formatNumber(edge.count);
        button.append(label, count);
        button.addEventListener("click", () => {
          state.networkSelected = neighbour.id;
          state.networkOverview = false;
          renderNetwork();
        });
        list.append(button);
      });
    elements.networkDetail.append(type, title, count, subhead, list);
  }

  function renderNetwork() {
    if (!elements.networkCanvas || !elements.networkDetail || !state.networkGraph) return;
    const graph = state.networkGraph;
    const visible = networkVisibleGraph(graph);
    const mobile = window.matchMedia("(max-width: 700px)").matches;
    const width = mobile ? 380 : 760;
    const height = mobile ? 500 : 510;
    const positions = networkPositions(visible.nodes, width, height, state.networkOverview);
    const maxEdge = Math.max(1, ...visible.edges.map((edge) => edge.count));
    const ns = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("role", "group");
    svg.setAttribute("aria-label", elements.networkCanvas.getAttribute("aria-label"));
    const title = document.createElementNS(ns, "title");
    title.textContent = elements.networkCanvas.getAttribute("aria-label");
    svg.append(title);

    const edgeLayer = document.createElementNS(ns, "g");
    edgeLayer.setAttribute("class", "library-network-edges");
    visible.edges.forEach((edge) => {
      const source = positions.get(edge.source);
      const target = positions.get(edge.target);
      if (!source || !target) return;
      const line = document.createElementNS(ns, "line");
      line.setAttribute("x1", source.x);
      line.setAttribute("y1", source.y);
      line.setAttribute("x2", target.x);
      line.setAttribute("y2", target.y);
      line.setAttribute("stroke-width", String(1.2 + 5.2 * edge.count / maxEdge));
      const edgeTitle = document.createElementNS(ns, "title");
      edgeTitle.textContent = copy.networkBooks(edge.count);
      line.append(edgeTitle);
      edgeLayer.append(line);
    });
    svg.append(edgeLayer);

    const nodeLayer = document.createElementNS(ns, "g");
    nodeLayer.setAttribute("class", "library-network-nodes");
    const maxNode = Math.max(1, ...visible.nodes.map((node) => node.count));
    visible.nodes.forEach((node) => {
      const position = positions.get(node.id);
      const selected = !state.networkOverview && node.id === state.networkSelected;
      const radius = Math.max(10, Math.min(selected ? 31 : 24, 9 + 20 * Math.sqrt(node.count / maxNode)));
      const group = document.createElementNS(ns, "g");
      group.setAttribute("class", `library-network-node is-${node.type}${selected ? " is-selected" : ""}`);
      group.setAttribute("transform", `translate(${position.x} ${position.y})`);
      group.setAttribute("role", "button");
      group.setAttribute("tabindex", "0");
      group.setAttribute("aria-label", `${networkTypeLabel(node.type)}: ${node.type === "theme" ? themeLabel(node.label) : node.label}, ${copy.networkBooks(node.count)}`);
      let shape;
      if (node.type === "publisher") {
        shape = document.createElementNS(ns, "rect");
        shape.setAttribute("x", String(-radius));
        shape.setAttribute("y", String(-radius));
        shape.setAttribute("width", String(radius * 2));
        shape.setAttribute("height", String(radius * 2));
        shape.setAttribute("rx", "3");
      } else {
        shape = document.createElementNS(ns, "circle");
        shape.setAttribute("r", String(radius));
      }
      const label = document.createElementNS(ns, "text");
      label.setAttribute("y", String(radius + (mobile ? 14 : 16)));
      label.setAttribute("text-anchor", "middle");
      const displayLabel = node.type === "theme" ? themeLabel(node.label) : node.label;
      label.textContent = displayLabel.length > (mobile ? 19 : 24) ? `${displayLabel.slice(0, mobile ? 17 : 22)}…` : displayLabel;
      const nodeTitle = document.createElementNS(ns, "title");
      nodeTitle.textContent = displayLabel;
      group.append(shape, label, nodeTitle);
      const selectNode = () => {
        state.networkSelected = node.id;
        state.networkOverview = false;
        renderNetwork();
      };
      group.addEventListener("click", selectNode);
      group.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectNode();
        }
      });
      nodeLayer.append(group);
    });
    svg.append(nodeLayer);
    elements.networkCanvas.replaceChildren(svg);
    renderNetworkDetail(graph, visible);
  }

  function selectNetworkSearchResult() {
    const query = normalize(elements.networkSearch.value);
    if (!query || !state.networkGraph) return;
    const match = Array.from(state.networkGraph.nodes.values())
      .filter((node) => node.type !== "theme" && normalize(node.label).includes(query))
      .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, locale))[0];
    if (!match) {
      elements.networkDetail.replaceChildren();
      const message = document.createElement("p");
      message.className = "library-network-empty";
      message.textContent = copy.networkSearchNone;
      elements.networkDetail.append(message);
      return;
    }
    state.networkSelected = match.id;
    state.networkOverview = false;
    renderNetwork();
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
      detailRow(copy.networkTheme, themeLabel(themeFor(record))),
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
    elements.themeReset?.addEventListener("click", () => {
      state.selectedTheme = "";
      renderThemeAtlas(state.records);
    });
    elements.timelineReset?.addEventListener("click", () => {
      state.timelineDecade = "";
      renderTimeline(state.records);
    });
    elements.timelinePrev?.addEventListener("click", () => {
      const groups = decadeGroups(state.records);
      const index = groups.findIndex((group) => String(group.decade) === String(state.timelineDecade));
      if (index > 0) {
        state.timelineDecade = String(groups[index - 1].decade);
        renderTimeline(state.records);
      }
    });
    elements.timelineNext?.addEventListener("click", () => {
      const groups = decadeGroups(state.records);
      const index = groups.findIndex((group) => String(group.decade) === String(state.timelineDecade));
      if (index >= 0 && index < groups.length - 1) {
        state.timelineDecade = String(groups[index + 1].decade);
        renderTimeline(state.records);
      }
    });
    elements.wallDecade?.addEventListener("change", (event) => {
      state.wallDecade = event.target.value;
      state.wallVisible = 32;
      renderCoverWall(state.records);
    });
    elements.wallTheme?.addEventListener("change", (event) => {
      state.wallTheme = event.target.value;
      state.wallVisible = 32;
      renderCoverWall(state.records);
    });
    elements.wallShuffle?.addEventListener("click", () => {
      state.wallSeed += 1;
      state.wallVisible = 32;
      renderCoverWall(state.records);
    });
    elements.wallMore?.addEventListener("click", () => {
      state.wallVisible += 32;
      renderCoverWall(state.records);
    });
    elements.networkRecenter?.addEventListener("click", () => {
      const largestTheme = themeGroups(state.records)[0]?.theme || "À classer";
      state.networkSelected = `theme:${normalize(largestTheme)}`;
      state.networkOverview = false;
      elements.networkSearch.value = "";
      renderNetwork();
    });
    elements.networkAll?.addEventListener("click", () => {
      state.networkOverview = true;
      renderNetwork();
    });
    elements.networkSearch?.addEventListener("search", selectNetworkSearchResult);
    elements.networkSearch?.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        selectNetworkSearchResult();
      }
    });
    let resizeTimer;
    window.addEventListener("resize", () => {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(renderNetwork, 160);
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
      const themes = themeGroups(state.records);
      const decades = decadeGroups(state.records);
      state.selectedTheme = themes[0]?.theme || "";
      state.timelineDecade = String(decades.slice().sort((a, b) => b.count - a.count)[0]?.decade || "");
      state.networkGraph = buildNetworkGraph(state.records);
      state.networkSelected = `theme:${normalize(state.selectedTheme || "À classer")}`;
      updateMetrics(state.records);
      renderShelf(state.records);
      renderDecadeChart(state.records);
      renderPublisherChart(state.records);
      renderThemeAtlas(state.records);
      renderTimeline(state.records);
      renderRarity(state.records);
      populateExplorationFilters(state.records);
      renderNetwork();
      renderCoverWall(state.records);
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
