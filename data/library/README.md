# Données de la bibliothèque

La base publique est reconstruite de façon reproductible à partir de cinq couches.

1. `clz-library-raw.json` conserve sans modification l’extraction du PDF CLZ.
2. Les caches Open Library, Google Books, éditeurs et libraires conservent les réponses externes utilisées pour les métadonnées et les couvertures.
3. `library-curation.json` décrit chaque correction manuelle, son niveau de confiance et ses sources.
4. `library-normalization.json` définit les alias d’auteurs et d’éditeurs ainsi que la politique de regroupement des doublons.
5. `library-themes.json` définit la classification thématique ordonnée appliquée aux seuls champs titre, genre et série, avec une catégorie de repli explicite.

La commande suivante produit `assets/library/library-data.json` et le rapport de qualité `library-quality-report.json`.

```bash
python3 scripts/curate_library_data.py
```

Lors d’un nouvel export CLZ, les identifiants des notices existantes sont préservés afin que les corrections manuelles et les couvertures sans ISBN restent associées au bon livre:

```bash
uv run --with pdfplumber python scripts/extract_clz_library.py \
  /chemin/vers/export-clz.pdf \
  data/library/clz-library-raw.json \
  --previous data/library/clz-library-raw.json
python3 scripts/curate_library_data.py
python3 scripts/fetch_openlibrary_isbn.py
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

Les couvertures supplémentaires vérifiées visuellement sont reconstruites dans un cache distinct. Les URL AbeBooks ne sont approuvées qu'après exclusion des images génériques portant la mention qu'elles ne représentent pas la véritable couverture. Les éditions sans ISBN exigent une concordance stricte du titre, de l'auteur, de l'année et de la maison d'édition:

```bash
python3 scripts/fetch_verified_covers.py
python3 scripts/curate_library_data.py
```

Règles de curation:

- une absence d’ISBN avant 1970 est classée comme attendue;
- une absence d’ISBN à partir de 1970 est signalée pour examen, mais n’est pas remplie avec l’ISBN d’une réimpression;
- les métadonnées Open Library ne remplissent que des champs CLZ vides et seulement après une correspondance exacte par ISBN;
- une valeur CLZ non vide n’est remplacée que par une correction manuelle à confiance élevée et sourcée;
- les champs CLZ d’origine restent disponibles dans `author` et `publisher`;
- les libellés d’affichage et d’analyse sont produits dans `author_normalized` et `publisher_normalized`;
- le thème est attribué par une règle versionnée; une notice sans indice explicite reste dans `À classer`;
- les auteurs répétés dans une même notice sont supprimés après normalisation;
- les notices partageant le même ISBN valide sont regroupées;
- deux notices sans ISBN distinct sont regroupées seulement si leur titre normalisé et leurs auteurs sont compatibles, sans conflit d’année, d’éditeur ni de collection;
- deux ISBN valides distincts ne sont jamais regroupés, même si le titre est identique;
- chaque regroupement conserve `source_record_ids`, `source_pages` et `source_record_count`, afin qu’aucune notice source ne soit perdue;
- le nombre de notices sources ne doit pas être interprété comme un nombre confirmé d’exemplaires physiques.

Le pipeline est validé par des tests de traçabilité, d’unicité et de déterminisme:

```bash
python3 scripts/test_library_data.py
```

Le cache Open Library est un instantané de travail et non une autorité bibliographique unique. Les corrections importantes reposent aussi sur les pages d’éditeurs, BAnQ, Springer, SIAM ou WorldCat indiquées dans `library-curation.json`.
