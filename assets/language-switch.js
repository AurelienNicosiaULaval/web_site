(function () {
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
  const siteRoot = rawPath.startsWith("/en/")
    ? "/"
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

    const targetUrl = `${siteRoot}${targetRel}`;
    const switcher = Array.from(document.querySelectorAll(".navbar-nav .nav-link")).find(
      (link) => (link.getAttribute("href") || "").includes("en/index.html")
    );

    if (!switcher) {
      return;
    }

    switcher.href = new URL(targetUrl, url).toString();
    const label = switcher.querySelector(".menu-text");
    if (label) {
      label.textContent = currentInEnglish ? "FR" : "EN";
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", updateSwitcher);
  } else {
    updateSwitcher();
  }
})();
