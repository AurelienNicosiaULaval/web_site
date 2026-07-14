# Données de la bibliothèque

La base publique est reconstruite de façon reproductible à partir de trois couches.

1. `clz-library-raw.json` conserve sans modification l’extraction du PDF CLZ.
2. Les caches Open Library, Google Books et Éditions Ellipses conservent les réponses externes utilisées pour les métadonnées et les couvertures.
3. `library-curation.json` décrit chaque correction manuelle, son niveau de confiance et ses sources.

La commande suivante produit `assets/library/library-data.json` et le rapport de qualité `library-quality-report.json`.

```bash
python3 scripts/curate_library_data.py
```

Les couvertures officielles Ellipses manquantes sont actualisées par ISBN exact avant la reconstruction:

```bash
python3 scripts/fetch_ellipses_covers.py
python3 scripts/curate_library_data.py
```

Les couvertures Dunod et les couvertures françaises de repli sont également actualisées par ISBN exact:

```bash
python3 scripts/fetch_dunod_covers.py
python3 scripts/fetch_lalibrairie_covers.py
python3 scripts/curate_library_data.py
```

Règles de curation:

- une absence d’ISBN avant 1970 est classée comme attendue;
- une absence d’ISBN à partir de 1970 est signalée pour examen, mais n’est pas remplie avec l’ISBN d’une réimpression;
- les métadonnées Open Library ne remplissent que des champs CLZ vides et seulement après une correspondance exacte par ISBN;
- une valeur CLZ non vide n’est remplacée que par une correction manuelle à confiance élevée et sourcée;
- les entrées pouvant représenter plusieurs exemplaires physiques sont conservées.

Le cache Open Library est un instantané de travail et non une autorité bibliographique unique. Les corrections importantes reposent aussi sur les pages d’éditeurs, BAnQ, Springer, SIAM ou WorldCat indiquées dans `library-curation.json`.
