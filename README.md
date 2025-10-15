# Site Quarto — Aurélien (ULaval)

Site web d'enseignant en mathématiques et statistiques, prêt à être publié sur **GitHub Pages**.

## Caractéristiques
- Navigation adaptée : Accueil, Enseignement, Ressources, **CDA (Centre)**, Blog, À propos, CV.
- Langue et locale : **fr-CA** (Québec).
- Thème `cosmo` + styles simples.
- Workflow **GitHub Actions** → branche `gh-pages`.

## Déploiement — Étapes

1. **Créer un dépôt** GitHub (ex. `site-aurelien-quarto`).  
2. **Télécharger et extraire** cette archive, puis :
   ```bash
   git init
   git branch -M main
   git add -A
   git commit -m "Initial commit: site Quarto (adapté ULaval)"
   git remote add origin https://github.com/<GITHUB_USERNAME>/<REPO_NAME>.git
   git push -u origin main
   ```
3. Éditez `_quarto.yml` et remplacez `<GITHUB_USERNAME>` et `<REPO_NAME>` dans `site-url` et `repo-url`.
4. **Activer GitHub Pages** : *Settings → Pages* → **Deploy from a branch** → branche `gh-pages`.
5. À chaque `git push` sur `main`, le site est rendu et publié automatiquement.

### Prévisualiser en local
```bash
quarto preview
```

### Personnalisation rapide
- Remplacez `assets/logo.svg` par votre logo.
- Mettez à jour **CDA** (`cda/index.qmd`) avec horaires, lieux, modalités et liens d'inscription.
- Ajoutez des dossiers dans `cours/` pour générer une page par cours.

---

© 2025 Aurélien — Université Laval
