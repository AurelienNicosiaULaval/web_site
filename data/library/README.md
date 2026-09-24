# Données de la bibliothèque

La base publique est reconstruite de façon reproductible à partir de cinq couches.

1. `clz-library-raw.json` conserve les champs bibliographiques de l’export CLZ, en CSV ou en PDF. L’import normalise uniquement les espaces et les caractères Unicode.
2. Les caches Open Library, Google Books, éditeurs et libraires conservent les réponses externes utilisées pour les métadonnées et les couvertures.
3. `library-curation.json` décrit chaque correction manuelle, son niveau de confiance et ses sources.
4. `library-normalization.json` définit les alias d’auteurs et d’éditeurs ainsi que la politique de regroupement des doublons.
5. `library-themes.json` définit la classification thématique ordonnée appliquée aux seuls champs titre, genre et série, avec une catégorie de repli explicite.

La commande suivante produit `assets/library/library-data.json` et le rapport de qualité `library-quality-report.json`.

```bash
python3 scripts/curate_library_data.py
python3 scripts/build_library_audit_artifact.py
```

Lors d’un nouvel export CLZ, les identifiants des notices existantes sont préservés afin que les corrections manuelles et les couvertures sans ISBN restent associées au bon livre:

```bash
python3 scripts/extract_clz_library.py \
  /chemin/vers/export-clz.csv \
  data/library/clz-library-raw.json \
  --previous data/library/clz-library-raw.json \
  --exported-on YYYY-MM-DD
python3 scripts/curate_library_data.py
python3 scripts/build_library_audit_artifact.py
```

Le CSV doit contenir `Author`, `Title`, `ISBN`, `Publisher`, `Publication Date`, `Genre`, `Publication Year` et `Series`. Les autres colonnes, notamment les notes et renseignements d’achat, ne sont pas importées. `source_rows` désigne les lignes logiques du CSV, en comptant l’en-tête comme ligne 1. La date de l’export est distincte de la date d’import dans le site.

L’instantané `clz-books-2026-09-16.csv` contient ces huit colonnes bibliographiques et 618 notices. L’import du 24 septembre conserve les 571 identifiants antérieurs, ajoute 47 notices et ne retire aucune notice. Les règles existantes regroupent 16 paires de notices, pour 602 fiches d’édition. Une valeur d’éditeur erronée (« 1970 ») est corrigée par correspondance exacte d’ISBN avec Google Books, avec sa source dans `library-curation.json`. Les champs sans information restent vides; les caches de métadonnées et de couvertures existants sont conservés.

Pour un export PDF:

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
- chaque regroupement conserve `source_record_ids`, `source_record_count` et les repères `source_pages` (PDF) ou `source_rows` (CSV), afin qu’aucune notice source ne soit perdue;
- le nombre de notices sources ne doit pas être interprété comme un nombre confirmé d’exemplaires physiques.

Le pipeline est validé par des tests de traçabilité, d’unicité et de déterminisme:

```bash
python3 scripts/test_library_data.py
```

Le cache Open Library est un instantané de travail et non une autorité bibliographique unique. Les corrections importantes reposent aussi sur les pages d’éditeurs, BAnQ, Springer, SIAM ou WorldCat indiquées dans `library-curation.json`.
