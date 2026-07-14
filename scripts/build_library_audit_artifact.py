#!/usr/bin/env python3
"""Build the canonical interactive data-quality report for the library."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "assets/library/library-data.json"
QUALITY = ROOT / "data/library/library-quality-report.json"
OUTPUT = ROOT / "data/library/library-audit-artifact.json"
GENERATED_AT = "2026-07-13"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def query_rows(connection: sqlite3.Connection, sql: str) -> list[dict[str, object]]:
    cursor = connection.execute(sql)
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def main() -> None:
    catalogue = read_json(CATALOGUE)
    quality = read_json(QUALITY)
    records_by_id = {record["id"]: record for record in catalogue["records"]}

    field_labels = {
        "author": "Auteur",
        "title": "Titre",
        "isbn": "ISBN",
        "publisher": "Éditeur",
        "publication_date": "Date de publication",
        "publication_year": "Année",
        "genre": "Genre CLZ",
        "series": "Collection",
    }
    correction_rows = []
    for applied in quality["applied_overrides"]:
        record = records_by_id[applied["id"]]
        correction_rows.append({
            "id": applied["id"],
            "title": record["title"],
            "changed_fields": ", ".join(field_labels.get(field, field) for field in applied["after"]),
            "source_count": len(applied["sources"]),
            "sources": ", ".join(applied["sources"]),
            "change_count": len(applied["after"]),
        })

    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE records (
          id TEXT PRIMARY KEY,
          author TEXT,
          title TEXT,
          isbn TEXT,
          publisher TEXT,
          publication_date TEXT,
          publication_year TEXT,
          genre TEXT,
          series TEXT,
          isbn_status TEXT,
          publisher_normalized TEXT,
          has_openlibrary INTEGER
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE raw_records (
          id TEXT PRIMARY KEY,
          author TEXT,
          title TEXT,
          isbn TEXT,
          publisher TEXT,
          publication_date TEXT,
          publication_year TEXT,
          genre TEXT,
          series TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE corrections (
          id TEXT PRIMARY KEY,
          title TEXT,
          changed_fields TEXT,
          source_count INTEGER,
          sources TEXT,
          change_count INTEGER
        )
        """
    )
    record_fields = [
        "id", "author", "title", "isbn", "publisher", "publication_date",
        "publication_year", "genre", "series", "isbn_status",
        "publisher_normalized",
    ]
    connection.executemany(
        "INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            tuple(record.get(field, "") for field in record_fields)
            + (1 if record.get("openlibrary") else 0,)
            for record in catalogue["records"]
        ],
    )
    raw_catalogue = read_json(ROOT / "data/library/clz-library-raw.json")
    raw_fields = [
        "id", "author", "title", "isbn", "publisher", "publication_date",
        "publication_year", "genre", "series",
    ]
    connection.executemany(
        "INSERT INTO raw_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [tuple(record.get(field, "") for field in raw_fields) for record in raw_catalogue["records"]],
    )
    connection.executemany(
        "INSERT INTO corrections VALUES (:id, :title, :changed_fields, :source_count, :sources, :change_count)",
        correction_rows,
    )

    summary_sql = """
    SELECT
      COUNT(*) AS records,
      SUM(CASE WHEN isbn_status = 'valid' THEN 1 ELSE 0 END) AS valid_isbn,
      1.0 * SUM(CASE WHEN isbn_status = 'valid' THEN 1 ELSE 0 END) / COUNT(*) AS valid_isbn_share,
      SUM(CASE WHEN isbn_status = 'missing_pre_1970' THEN 1 ELSE 0 END) AS expected_pre1970_missing,
      SUM(CASE WHEN isbn_status IN ('missing_1970_or_later', 'missing_unknown_year') THEN 1 ELSE 0 END) AS isbn_to_review,
      (SELECT COUNT(*) FROM corrections) AS corrected_records,
      (SELECT SUM(change_count) FROM corrections) AS changed_fields,
      1.0 * COUNT(DISTINCT CASE WHEN isbn_status = 'valid' AND has_openlibrary = 1 THEN isbn END)
        / COUNT(DISTINCT CASE WHEN isbn_status = 'valid' THEN isbn END) AS external_isbn_coverage,
      (SELECT COUNT(DISTINCT publisher) FROM raw_records WHERE TRIM(publisher) <> '') AS raw_publishers,
      COUNT(DISTINCT CASE WHEN TRIM(publisher_normalized) <> '' THEN publisher_normalized END) AS normalized_publishers
    FROM records
    """.strip()
    isbn_status_sql = """
    WITH status_labels(status_key, status, review_required, sort_order) AS (
      VALUES
        ('valid', 'ISBN valide', 'Non', 1),
        ('missing_pre_1970', 'Absent, avant 1970', 'Non', 2),
        ('missing_1970_or_later', 'Absent, 1970 ou après', 'Oui', 3),
        ('missing_unknown_year', 'Absent, année inconnue', 'Oui', 4)
    )
    SELECT labels.status, COUNT(records.id) AS count, labels.review_required
    FROM status_labels AS labels
    LEFT JOIN records ON records.isbn_status = labels.status_key
    GROUP BY labels.status_key, labels.status, labels.review_required, labels.sort_order
    ORDER BY labels.sort_order
    """.strip()
    missing_fields_sql = """
    WITH fields(field_key, field, sort_order) AS (
      VALUES
        ('author', 'Auteur', 1),
        ('title', 'Titre', 2),
        ('isbn', 'ISBN', 3),
        ('publisher', 'Éditeur', 4),
        ('publication_date', 'Date de publication', 5),
        ('publication_year', 'Année', 6),
        ('genre', 'Genre CLZ', 7),
        ('series', 'Collection', 8)
    ), counts AS (
      SELECT 'author' AS field_key,
             (SELECT SUM(TRIM(author) = '') FROM raw_records) AS raw_missing,
             (SELECT SUM(TRIM(author) = '') FROM records) AS curated_missing
      UNION ALL SELECT 'title', (SELECT SUM(TRIM(title) = '') FROM raw_records), (SELECT SUM(TRIM(title) = '') FROM records)
      UNION ALL SELECT 'isbn', (SELECT SUM(TRIM(isbn) = '') FROM raw_records), (SELECT SUM(TRIM(isbn) = '') FROM records)
      UNION ALL SELECT 'publisher', (SELECT SUM(TRIM(publisher) = '') FROM raw_records), (SELECT SUM(TRIM(publisher) = '') FROM records)
      UNION ALL SELECT 'publication_date', (SELECT SUM(TRIM(publication_date) = '') FROM raw_records), (SELECT SUM(TRIM(publication_date) = '') FROM records)
      UNION ALL SELECT 'publication_year', (SELECT SUM(TRIM(publication_year) = '') FROM raw_records), (SELECT SUM(TRIM(publication_year) = '') FROM records)
      UNION ALL SELECT 'genre', (SELECT SUM(TRIM(genre) = '') FROM raw_records), (SELECT SUM(TRIM(genre) = '') FROM records)
      UNION ALL SELECT 'series', (SELECT SUM(TRIM(series) = '') FROM raw_records), (SELECT SUM(TRIM(series) = '') FROM records)
    )
    SELECT fields.field, counts.raw_missing, counts.curated_missing,
           counts.raw_missing - counts.curated_missing AS resolved
    FROM fields
    JOIN counts USING (field_key)
    ORDER BY fields.sort_order
    """.strip()
    review_cases_sql = """
    SELECT
      id,
      CASE WHEN TRIM(publication_year) = '' THEN 'Inconnue' ELSE publication_year END AS year,
      CASE WHEN TRIM(title) = '' THEN 'Titre non renseigné' ELSE title END AS title,
      CASE WHEN TRIM(author) = '' THEN 'Auteur non renseigné' ELSE author END AS author,
      CASE isbn_status
        WHEN 'missing_1970_or_later' THEN 'Absent, 1970 ou après'
        WHEN 'missing_unknown_year' THEN 'Absent, année inconnue'
      END AS reason
    FROM records
    WHERE isbn_status IN ('missing_1970_or_later', 'missing_unknown_year')
    ORDER BY CASE WHEN publication_year = '' THEN 9999 ELSE CAST(publication_year AS INTEGER) END, id
    """.strip()
    correction_log_sql = """
    SELECT id, title, changed_fields, source_count, sources
    FROM corrections
    ORDER BY id
    """.strip()

    summary = query_rows(connection, summary_sql)
    isbn_status_rows = query_rows(connection, isbn_status_sql)
    missing_field_rows = query_rows(connection, missing_fields_sql)
    review_rows = query_rows(connection, review_cases_sql)
    correction_rows = query_rows(connection, correction_log_sql)
    connection.close()

    sources = [
        {
            "id": "clz_raw",
            "label": "Extraction brute du PDF CLZ Books",
            "path": "data/library/clz-library-raw.json",
        },
        {
            "id": "quality_pipeline",
            "label": "Rapport de qualité produit par le pipeline de curation",
            "path": "data/library/library-quality-report.json",
        },
        {
            "id": "summary_sql",
            "label": "Indicateurs synthétiques du catalogue curé",
            "query": {
                "engine": "SQLite",
                "language": "sql",
                "executed_at": GENERATED_AT,
                "description": "Calcule les indicateurs synthétiques à partir des notices brutes, curées et du journal de corrections.",
                "sql": summary_sql,
                "tables_used": ["records", "raw_records", "corrections"],
                "metric_definitions": [
                    "ISBN valide: notice dont isbn_status vaut valid après contrôle de somme.",
                    "ISBN à vérifier: ISBN absent en 1970 ou après, ou année inconnue.",
                    "Couverture externe: ISBN valides distincts possédant une notice Open Library exacte, divisés par tous les ISBN valides distincts.",
                ],
            },
        },
        {
            "id": "isbn_status_sql",
            "label": "Répartition des statuts ISBN",
            "query": {
                "engine": "SQLite",
                "language": "sql",
                "executed_at": GENERATED_AT,
                "description": "Compte les notices dans chacun des quatre statuts ISBN.",
                "sql": isbn_status_sql,
                "tables_used": ["records"],
                "metric_definitions": ["Nombre de notices par statut ISBN après curation."],
            },
        },
        {
            "id": "missing_fields_sql",
            "label": "Champs manquants avant et après curation",
            "query": {
                "engine": "SQLite",
                "language": "sql",
                "executed_at": GENERATED_AT,
                "description": "Compare les valeurs vides dans l’extraction CLZ et dans le catalogue curé.",
                "sql": missing_fields_sql,
                "tables_used": ["raw_records", "records"],
                "metric_definitions": ["Complétés: nombre brut de valeurs vides moins le nombre curé."],
            },
        },
        {
            "id": "review_cases_sql",
            "label": "Notices dont l’ISBN reste à vérifier",
            "query": {
                "engine": "SQLite",
                "language": "sql",
                "executed_at": GENERATED_AT,
                "description": "Liste les publications de 1970 ou après sans ISBN et les publications sans année ni ISBN.",
                "sql": review_cases_sql,
                "tables_used": ["records"],
            },
        },
        {
            "id": "correction_log_sql",
            "label": "Journal des corrections manuelles",
            "query": {
                "engine": "SQLite",
                "language": "sql",
                "executed_at": GENERATED_AT,
                "description": "Liste les champs réellement changés et le nombre de sources pour chaque notice corrigée.",
                "sql": correction_log_sql,
                "tables_used": ["corrections"],
            },
        },
        {
            "id": "curation_rules",
            "label": "Corrections manuelles et provenance bibliographique",
            "path": "data/library/library-curation.json",
        },
        {
            "id": "isbn_agency",
            "label": "International ISBN Agency, historique du SBN et de l’ISBN",
            "href": "https://www.isbn-international.org/sites/default/files/BIC%20Bites%20International%20Standard%20Book%20Number_FINAL.pdf",
        },
    ]

    manifest = {
        "version": 1,
        "surface": "report",
        "title": "Audit de qualité de la bibliothèque",
        "description": "État de la base CLZ après validation, enrichissement bibliographique et normalisation.",
        "generatedAt": GENERATED_AT,
        "cards": [
            {
                "id": "catalogue_size",
                "description": "Taille de la collection conservée après curation.",
                "dataset": "summary",
                "sourceId": "summary_sql",
                "metrics": [{"label": "Notices conservées", "field": "records", "format": "number"}],
            },
            {
                "id": "isbn_validity",
                "description": "Présence et validité des identifiants après correction.",
                "dataset": "summary",
                "sourceId": "summary_sql",
                "metrics": [
                    {"label": "ISBN valides", "field": "valid_isbn", "format": "number"},
                    {"label": "Part du catalogue", "field": "valid_isbn_share", "format": "percent"},
                ],
            },
            {
                "id": "curation_changes",
                "description": "Corrections manuelles à confiance élevée et sourcées.",
                "dataset": "summary",
                "sourceId": "summary_sql",
                "metrics": [
                    {"label": "Notices corrigées", "field": "corrected_records", "format": "number"},
                    {"label": "Champs modifiés", "field": "changed_fields", "format": "number"},
                ],
            },
            {
                "id": "remaining_review",
                "description": "Cas qui ne peuvent pas être complétés sans identifier l’édition physique.",
                "dataset": "summary",
                "sourceId": "summary_sql",
                "metrics": [{"label": "ISBN à vérifier", "field": "isbn_to_review", "format": "number"}],
            },
        ],
        "charts": [
            {
                "id": "isbn_status_chart",
                "title": "Statut des ISBN dans le catalogue curé",
                "subtitle": "Parmi les 99 ISBN absents, 86 concernent des publications antérieures à 1970 et 13 cas restent à examiner.",
                "question": "Comment la complétude des ISBN se répartit-elle selon la période de publication?",
                "rationale": "Un diagramme en barres compare directement les quatre statuts sur une base zéro.",
                "type": "bar",
                "dataset": "isbn_status",
                "sourceId": "isbn_status_sql",
                "encodings": {
                    "x": {"field": "status", "type": "nominal", "label": "Statut"},
                    "y": {"field": "count", "type": "quantitative", "label": "Nombre de notices", "format": "number"},
                },
                "yAxisTitle": "Nombre de notices",
                "valueFormat": "number",
                "layout": "full",
            }
        ],
        "tables": [
            {
                "id": "missing_fields_table",
                "title": "Champs manquants avant et après curation",
                "subtitle": "Les genres CLZ restent volontairement inchangés, car la taxonomie externe n’est pas homogène.",
                "dataset": "missing_fields",
                "sourceId": "missing_fields_sql",
                "defaultSort": {"field": "resolved", "direction": "desc"},
                "density": "dense",
                "columns": [
                    {"field": "field", "label": "Champ", "type": "text"},
                    {"field": "raw_missing", "label": "Manquants, brut", "format": "number"},
                    {"field": "curated_missing", "label": "Manquants, curé", "format": "number"},
                    {"field": "resolved", "label": "Complétés", "format": "number"},
                ],
            },
            {
                "id": "review_cases_table",
                "title": "Cas d’ISBN restant à examiner",
                "subtitle": "Aucun ISBN de réimpression n’a été attribué à une édition ancienne sans preuve.",
                "dataset": "review_cases",
                "sourceId": "review_cases_sql",
                "defaultSort": {"field": "year", "direction": "asc"},
                "density": "dense",
                "columns": [
                    {"field": "id", "label": "ID", "type": "text"},
                    {"field": "year", "label": "Année", "type": "text"},
                    {"field": "title", "label": "Titre", "type": "text"},
                    {"field": "author", "label": "Auteur", "type": "text"},
                    {"field": "reason", "label": "Motif", "type": "text"},
                ],
            },
            {
                "id": "correction_log_table",
                "title": "Journal des corrections manuelles",
                "subtitle": "Chaque modification remplace une valeur CLZ uniquement lorsque la correspondance bibliographique est jugée élevée.",
                "dataset": "correction_log",
                "sourceId": "correction_log_sql",
                "defaultSort": {"field": "id", "direction": "asc"},
                "density": "dense",
                "columns": [
                    {"field": "id", "label": "ID", "type": "text"},
                    {"field": "title", "label": "Titre curé", "type": "text"},
                    {"field": "changed_fields", "label": "Champs modifiés", "type": "text"},
                    {"field": "source_count", "label": "Sources", "format": "number"},
                ],
            },
        ],
        "sources": sources,
        "blocks": [
            {"id": "title", "type": "markdown", "body": "# Audit de qualité de la bibliothèque"},
            {
                "id": "executive_summary",
                "type": "markdown",
                "sourceId": "quality_pipeline",
                "body": "## Executive Summary\n\nLa base conserve les 467 notices CLZ et ne contient plus aucun ISBN invalide. Seize notices ont reçu des corrections manuelles à confiance élevée, soit 50 champs réellement modifiés. Après curation, 368 notices ont un ISBN valide. Parmi les 99 ISBN absents, 86 sont associés à des ouvrages publiés avant 1970; les 13 autres cas restent explicitement signalés plutôt que complétés avec une édition incertaine.",
            },
            {"id": "metrics", "type": "metric-strip", "cardIds": ["catalogue_size", "isbn_validity", "curation_changes", "remaining_review"]},
            {"id": "isbn_chart", "type": "chart", "chartId": "isbn_status_chart", "layout": "full"},
            {
                "id": "quality_improvements",
                "type": "markdown",
                "sourceId": "quality_pipeline",
                "body": "## Améliorations mesurables\n\nLes valeurs manquantes ont diminué pour les auteurs, titres, ISBN, éditeurs, dates et collections. La normalisation analytique ramène 205 libellés d’éditeur à 189 maisons d’édition, tout en conservant le libellé CLZ original dans chaque notice.",
            },
            {"id": "missing_fields", "type": "table", "tableId": "missing_fields_table", "layout": "full"},
            {
                "id": "remaining_cases",
                "type": "markdown",
                "sourceId": "isbn_agency",
                "body": "## Cas restant à examiner\n\nLa règle de travail classe l’absence d’ISBN avant 1970 comme attendue. Le SBN a commencé au Royaume-Uni en 1967 et la norme internationale ISBN a été approuvée en 1970. Pour les publications ultérieures, l’absence peut encore être légitime selon l’édition; une vérification de la page de copyright du livre physique serait nécessaire pour trancher les 13 cas signalés.",
            },
            {"id": "review_cases", "type": "table", "tableId": "review_cases_table", "layout": "full"},
            {
                "id": "corrections",
                "type": "markdown",
                "sourceId": "curation_rules",
                "body": "## Corrections appliquées\n\nLes changements majeurs comprennent deux ISBN nettoyés, deux titres qui ne correspondaient pas à leur ISBN, quatre années d’édition corrigées, des auteurs complétés et la rectification du nom Gérard A. Philippin. Les doublons possibles sont conservés, car ils peuvent représenter plusieurs exemplaires physiques.",
            },
            {"id": "correction_log", "type": "table", "tableId": "correction_log_table", "layout": "full"},
            {
                "id": "methodology",
                "type": "markdown",
                "sourceId": "curation_rules",
                "body": "## Méthodologie et limites\n\nLa couche CLZ brute est immuable. Open Library ne complète que les champs vides après une correspondance exacte par ISBN. Une valeur existante n’est remplacée que par une règle manuelle à confiance élevée et sourcée. La couverture Open Library atteint 66,1 % des 360 ISBN valides distincts. Les sujets externes sont conservés comme information secondaire, mais le genre CLZ n’est pas imputé automatiquement, car les vocabulaires ne sont pas comparables.",
            },
        ],
    }

    artifact = {
        "surface": "report",
        "manifest": manifest,
        "snapshot": {
            "version": 1,
            "generatedAt": GENERATED_AT,
            "status": "ready",
            "datasets": {
                "summary": summary,
                "isbn_status": isbn_status_rows,
                "missing_fields": missing_field_rows,
                "review_cases": review_rows,
                "correction_log": correction_rows,
            },
        },
        "sources": sources,
        "package_info": {
            "root": str(ROOT),
            "manifestPath": "data/library/library-audit-artifact.json",
            "snapshotPath": "data/library/library-audit-artifact.json",
        },
    }
    write_json(OUTPUT, artifact)
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(review_rows)} review cases.")


if __name__ == "__main__":
    main()
