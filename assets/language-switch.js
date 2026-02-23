<script>
(function () {
  const NAV_ITEMS = [
    { fr: "index.html", en: "index.html", frLabel: "Accueil", enLabel: "Home" },
    { fr: "enseignement.html", en: "enseignement.html", frLabel: "Enseignement", enLabel: "Teaching" },
    { fr: "recherche.html", en: "recherche.html", frLabel: "Recherche", enLabel: "Research" },
    { fr: "innovation.html", en: "innovation.html", frLabel: "Innovation Pédagogique", enLabel: "Educational innovation" },
    { fr: "ressources.html", en: "ressources.html", frLabel: "Autres", enLabel: "Resources" },
    { fr: "a-propos.html", en: "a-propos.html", frLabel: "A propos", enLabel: "About" },
    { fr: "cv/index.html", en: "cv/index.html", frLabel: "CV", enLabel: "CV" }
  ];

  const EN_PAGES = new Set([
    "index.html",
    "enseignement.html",
    "recherche.html",
    "innovation.html",
    "ressources.html",
    "a-propos.html",
    "publications.html",
    "cv/index.html",
    "cda/index.html"
  ]);

  const url = new URL(window.location.href);
  const rawPath = url.pathname;
  const enMarker = rawPath.indexOf("/en/");
  const siteRoot = enMarker >= 0
    ? rawPath.slice(0, enMarker + 1)
    : rawPath.match(/^\/[^/]+\//)?.[0] || "/";

  function toSiteRelative(pathname) {
    if (!pathname.startsWith(siteRoot)) {
      return pathname.replace(/^\//, "");
    }
    return pathname.slice(siteRoot.length);
  }

  function asIndex(pathname) {
    return pathname === "" ? "index.html" : pathname.replace(/\/$/, "index.html");
  }

  function isEnglishPage(pathname) {
    return pathname.startsWith("en/");
  }

  function findLanguageSwitcher(navLinks) {
    const labeled = navLinks.find((link) => {
      const text = (link.querySelector(".menu-text") || link).textContent || "";
      const code = text.trim().toUpperCase();
      return code === "EN" || code === "FR";
    });
    return labeled || navLinks[navLinks.length - 1] || null;
  }

  function setMenuText(link, text) {
    const label = link.querySelector(".menu-text");
    if (label) {
      label.textContent = text;
    }
  }

  function toAbsolute(relPath) {
    return new URL(`${siteRoot}${relPath}`, url).toString();
  }

  function updateSwitcher() {
    const relPath = asIndex(toSiteRelative(rawPath));
    const currentInEnglish = isEnglishPage(relPath);
    const frPage = currentInEnglish ? relPath.replace(/^en\//, "") : relPath;
    const targetRel = currentInEnglish
      ? EN_PAGES.has(frPage)
        ? frPage
        : "index.html"
      : EN_PAGES.has(frPage)
        ? `en/${frPage}`
        : "en/index.html";

    const navLinks = Array.from(document.querySelectorAll(".navbar-nav .nav-link"));
    const switcher = findLanguageSwitcher(navLinks);

    if (!switcher) {
      return;
    }

    const primaryNavLinks = navLinks.filter((link) => link !== switcher).slice(0, NAV_ITEMS.length);
    primaryNavLinks.forEach((link, i) => {
      const item = NAV_ITEMS[i];
      if (!item) {
        return;
      }
      const target = currentInEnglish ? `en/${item.en}` : item.fr;
      const label = currentInEnglish ? item.enLabel : item.frLabel;
      link.href = toAbsolute(target);
      setMenuText(link, label);
    });

    switcher.href = toAbsolute(targetRel);
    setMenuText(switcher, currentInEnglish ? "FR" : "EN");

    const searchBox = document.querySelector("#quarto-search");
    if (searchBox) {
      searchBox.setAttribute("title", currentInEnglish ? "Search" : "Recherche");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", updateSwitcher);
  } else {
    updateSwitcher();
  }
})();
</script>
