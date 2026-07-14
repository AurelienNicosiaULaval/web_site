# Données de la bibliothèque

La base publique est reconstruite de façon reproductible à partir de trois couches.

1. `clz-library-raw.json` conserve sans modification l’extraction du PDF CLZ.
2. `openlibrary-isbn-cache.json` et `openlibrary-missing-isbn-candidates.json` conservent les réponses externes consultées le 13 juillet 2026.
3. `library-curation.json` décrit chaque correction manuelle, son niveau de confiance et ses sources.

La commande suivante produit `assets/library/library-data.json` et le rapport de qualité `library-quality-report.json`.

```bash
python3 scripts/curate_library_data.py
```

Règles de curation:

- une absence d’ISBN avant 1970 est classée comme attendue;
- une absence d’ISBN à partir de 1970 est signalée pour examen, mais n’est pas remplie avec l’ISBN d’une réimpression;
- les métadonnées Open Library ne remplissent que des champs CLZ vides et seulement après une correspondance exacte par ISBN;
- une valeur CLZ non vide n’est remplacée que par une correction manuelle à confiance élevée et sourcée;
- les entrées pouvant représenter plusieurs exemplaires physiques sont conservées.

Le cache Open Library est un instantané de travail et non une autorité bibliographique unique. Les corrections importantes reposent aussi sur les pages d’éditeurs, BAnQ, Springer, SIAM ou WorldCat indiquées dans `library-curation.json`.
