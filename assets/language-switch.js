<script>
(() => {
  // Pair existing pages and keep untranslated documents explicitly in French.
  const paired = ['index.html','recherche.html','enseignement.html','research-lab.html','packages.html','innovation.html','ressources.html','a-propos.html','publications.html','cv/index.html','cda/index.html','packages/circularregression.html','packages/donutmap.html','packages/ggcircular.html','packages/tutorizeR.html','packages/glbfp.html','packages/leaflet-indoor.html','packages/lmmix.html','packages/ulavalssd.html','plan-du-site.html'];
  const pairs = new Map(paired.map(path => [path,path]));
  pairs.set('bibliotheque.html','library.html');
  const labels = new Map([
    ['Recherche','Research'],['Enseignement','Teaching'],['Logiciels','Software'],['Ressources','Resources'],['À propos','About'],['CV','CV'],
    ['Programme de recherche','Research program'],['Publications et prépublications','Publications and preprints'],['Projets ouverts','Open projects'],['Communications et thèse','Presentations and thesis'],
    ['Cours et démarche','Courses and approach'],['Encadrement','Supervision'],['Innovation pédagogique','Teaching innovation'],['CDA et GPT-CDA','CDA and GPT-CDA'],
    ['Catalogue des logiciels','Software catalogue'],['Packages R','R packages'],['Projets en développement','Development projects'],['Contributions','Contributions'],
    ['Données et supports','Datasets and materials'],['Présentations et ateliers','Presentations and workshops'],['Bibliothèque','Library'],['Explorations','Explorations'],['Actualités','Updates'],['Billets (français)','Posts (French)'],
    ['Profil et parcours','Profile and background'],['Médias et distinctions','Media and awards'],['Contact','Contact']
  ]);
  const anchors = new Map([
    ['encadrement','supervision'],['thèse-de-doctorat','doctoral-thesis'],['packages-sur-le-cran','packages-on-cran'],['projets-github-liés','related-github-projects'],
    ['contributions-open-source-externes','external-open-source-contributions'],['donnees-ressources','data-resources'],['actualités-et-points-forts','updates-and-highlights'],['rayonnement','outreach'],['profil','profile']
  ]);
  function init() {
    const brand = document.querySelector('a.navbar-brand');
    if (!brand) return;
    const home = new URL(brand.getAttribute('href'),location.href);
    const root = home.pathname.replace(/index\.html$/,'').replace(/en\/$/,'');
    const relative = location.pathname.slice(root.length).replace(/^\//,'');
    const english = relative.startsWith('en/');
    const current = (english ? relative.slice(3) : relative).replace(/\/$/,'/index.html') || 'index.html';
    const absolute = path => new URL(root + path,location.origin).href;
    const pagePath = path => absolute(english && pairs.has(path) ? 'en/' + pairs.get(path) : path);
    const parents = new Map([
      ['research-lab.html',['recherche.html','Recherche','Research']],
      ['innovation.html',['enseignement.html','Enseignement','Teaching']],
      ['cda/index.html',['enseignement.html','Enseignement','Teaching']],
      ['publications.html',['a-propos.html','À propos','About']],
      ['cv/index.html',['a-propos.html','À propos','About']],
      ['bibliotheque.html',['ressources.html','Ressources','Resources']],
      ['library.html',['ressources.html','Ressources','Resources']],
      ['blog/index.html',['ressources.html','Ressources','Resources']],
      ['presentations/au-dela-du-prompt/index.html',['innovation.html','Innovation pédagogique','Teaching innovation']]
    ]);
    if (current.startsWith('packages/')) parents.set(current,['packages.html','Logiciels','Software']);
    if (current.startsWith('blog/posts/')) parents.set(current,['blog/index.html','Billets','Posts (French)']);
    const main = document.querySelector('main');
    const title = main?.querySelector('h1') || document.querySelector('#title-block-header h1');
    if (current !== 'index.html' && main && title) {
      const navigation = document.createElement('nav');
      navigation.className = 'page-breadcrumbs';
      navigation.setAttribute('aria-label',english ? 'Breadcrumb' : 'Fil d’Ariane');
      const list = document.createElement('ol');
      const addLink = (label,path) => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.textContent = label;
        link.href = pagePath(path);
        item.append(link);
        list.append(item);
      };
      addLink(english ? 'Home' : 'Accueil','index.html');
      const parent = parents.get(current);
      if (parent) addLink(parent[english ? 2 : 1],parent[0]);
      const item = document.createElement('li');
      item.textContent = title.textContent.trim();
      item.setAttribute('aria-current','page');
      list.append(item);
      navigation.append(list);
      const illustratedHeader = document.querySelector('.site-page-header');
      if (illustratedHeader) illustratedHeader.before(navigation);
      else main.prepend(navigation);
    }
    document.querySelectorAll('.nav-footer a').forEach(link => {
      if (link.textContent.trim() !== 'Plan du site') return;
      link.textContent = english ? 'Sitemap' : 'Plan du site';
      link.href = pagePath('plan-du-site.html');
    });
    document.querySelectorAll('a.navbar-brand').forEach(link => {
      link.href = absolute(english ? 'en/index.html' : 'index.html');
      if (link.querySelector('img')) link.setAttribute('aria-label',english ? 'Home' : 'Accueil');
    });
    document.querySelectorAll('.navbar a:not(.navbar-brand)').forEach(link => {
      const label = link.querySelector('.menu-text') || link;
      const rawLabel = label.textContent.trim();
      if (rawLabel === 'FR / EN') {
        const pair = english ? [...pairs.entries()].find(([,value]) => value === current)?.[0] : pairs.get(current);
        link.href = absolute(pair ? (english ? pair : 'en/' + pair) : (english ? 'index.html' : 'en/index.html'));
        link.classList.add('language-switch');
        link.setAttribute('aria-label',english ? 'Lire cette page en français' : 'Read this page in English');
        label.innerHTML = `<span class="${english ? '' : 'language-switch-current'}">FR</span><span class="language-switch-separator" aria-hidden="true">/</span><span class="${english ? 'language-switch-current' : ''}">EN</span>`;
        return;
      }
      if (english && labels.has(rawLabel)) label.textContent = labels.get(rawLabel);
      const href = link.getAttribute('href');
      if (!href || href.startsWith('#')) return;
      const target = new URL(href,location.href);
      if (target.origin !== location.origin || !target.pathname.startsWith(root)) return;
      let path = target.pathname.slice(root.length).replace(/^en\//,'').replace(/\/$/,'/index.html') || 'index.html';
      if (!pairs.has(path)) return;
      path = english ? 'en/' + pairs.get(path) : path;
      if (english && target.hash) {
        const anchor = decodeURIComponent(target.hash.slice(1));
        if (anchors.has(anchor)) target.hash = anchors.get(anchor);
      }
      link.href = absolute(path) + target.hash;
    });
    if (english) {
      const search = document.querySelector('#quarto-search');
      if (search) search.setAttribute('title','Search');
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',init);
  else init();
  // Keep navigation within the site in the current tab after Quarto initializes.
  window.addEventListener('load',() => {
    // Apply the footer destination after Quarto has normalized site links.
    const english = document.documentElement.lang.startsWith('en');
    const brand = document.querySelector('a.navbar-brand');
    if (brand) {
      const home = new URL(brand.href,location.href);
      const root = home.pathname.replace(/(?:en\/)?index\.html$/,'').replace(/en\/$/,'');
      document.querySelectorAll('.nav-footer a').forEach(link => {
        if (!['Plan du site','Sitemap'].includes(link.textContent.trim())) return;
        const href = new URL(root + (english ? 'en/' : '') + 'plan-du-site.html',location.origin).href;
        link.textContent = english ? 'Sitemap' : 'Plan du site';
        link.href = href;
        link.dataset.originalHref = href;
      });
    }
    const searchButton = document.querySelector('#quarto-search button');
    if (searchButton) searchButton.setAttribute('aria-label',document.documentElement.lang.startsWith('en') ? 'Search' : 'Rechercher');
    document.querySelectorAll('a[target="_blank"]').forEach(link => {
      if (new URL(link.href,location.href).origin === location.origin) link.removeAttribute('target');
    });
  });
})();
</script>
