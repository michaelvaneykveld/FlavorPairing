"""Process Flavor Matrix JSON exports into tabular files for graph ingestion.

Usage:
    python scripts/process_flavor_matrix.py

The script scans `docs/flavor-matrix-processed/` for `.json` files (or a single
array JSON), validates the schema, and emits CSV artifacts under
`build/flavor-matrix/`:
    - ingredients.csv
    - pairings.csv
    - substitutes.csv
    - matrix_nodes.csv
    - matrix_edges.csv
It also writes a simple processing report (`report.txt`) summarising counts and
any validation warnings.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

REQUIRED_FIELDS = {
    "ingredient",
    "page_reference",
    "summary",
    "best_pairings",
    "surprise_pairings",
    "substitutes",
    "additional_notes",
    "matrix_nodes",
    "matrix_edges",
    "uncertainties",
}

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "docs" / "flavor-matrix-processed"
OUTPUT_DIR = ROOT / "build" / "flavor-matrix"


@dataclass
class Record:
    data: Dict[str, Any]
    source: Path


def load_records(input_path: Path) -> List[Record]:
    records: List[Record] = []
    if input_path.is_file() and input_path.suffix.lower() == ".json":
        records.extend(_records_from_file(input_path))
        return records

    if not input_path.exists():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    json_files = sorted(input_path.glob("*.json"))
    for json_file in json_files:
        records.extend(_records_from_file(json_file))
    return records


def _records_from_file(path: Path) -> List[Record]:
    with path.open(encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError(f"JSON root must be dict or list in {path}")

    records: List[Record] = []
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Entry {idx} in {path} is not an object")
        records.append(Record(item, path))
    return records


def validate_record(record: Record) -> List[str]:
    data = record.data
    missing = REQUIRED_FIELDS - data.keys()
    warnings: List[str] = []
    if missing:
        warnings.append(
            f"{record.source.name}: missing fields {sorted(missing)} "
            f"for ingredient '{data.get('ingredient', '<unknown>')}'"
        )
    for key in ("best_pairings", "surprise_pairings", "substitutes", "additional_notes"):
        value = data.get(key)
        if value is not None and not isinstance(value, list):
            warnings.append(
                f"{record.source.name}: field '{key}' expected list "
                f"(ingredient '{data.get('ingredient', '<unknown>')}')"
            )
    for key in ("matrix_nodes", "matrix_edges"):
        value = data.get(key)
        if value is not None and not isinstance(value, list):
            warnings.append(
                f"{record.source.name}: field '{key}' expected list of objects "
                f"(ingredient '{data.get('ingredient', '<unknown>')}')"
            )
    return warnings


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    ensure_output_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def build_outputs(records: List[Record]) -> Dict[str, int]:
    ensure_output_dir(OUTPUT_DIR)
    counts = defaultdict(int)

    ingredient_rows = []
    pairing_rows = []
    substitute_rows = []
    node_rows = []
    edge_rows = []

    for record in records:
        data = record.data
        ingredient = data.get("ingredient")
        if not ingredient:
            continue

        page_reference = data.get("page_reference", "")
        summary = data.get("summary", "")
        notes = data.get("additional_notes") or []
        note_text = " | ".join(str(note) for note in notes) if notes else ""
        uncertainties = data.get("uncertainties") or []
        uncertainty_text = " | ".join(str(item) for item in uncertainties)

        ingredient_rows.append(
            [
                ingredient,
                page_reference,
                summary,
                note_text,
                uncertainty_text,
                record.source.name,
            ]
        )
        counts["ingredients"] += 1

        for pairing, tier in _iter_pairings(
            ingredient, data.get("best_pairings"), data.get("surprise_pairings")
        ):
            pairing_rows.append(
                [
                    ingredient,
                    pairing["target"],
                    pairing["tier"],
                    pairing["source"],
                ]
            )
            counts["pairings"] += 1

        for substitute in data.get("substitutes") or []:
            substitute_rows.append(
                [
                    ingredient,
                    substitute,
                    record.source.name,
                ]
            )
            counts["substitutes"] += 1

        for node in data.get("matrix_nodes") or []:
            node_rows.append(
                [
                    ingredient,
                    node.get("label", ""),
                    node.get("color", ""),
                    node.get("relative_size", ""),
                    node.get("legend_code", ""),
                    node.get("notes", ""),
                    record.source.name,
                ]
            )
            counts["matrix_nodes"] += 1

        for edge in data.get("matrix_edges") or []:
            node_rows_source = edge.get("source", "")
            node_rows_target = edge.get("target", "")
            edge_rows.append(
                [
                    ingredient,
                    node_rows_source,
                    node_rows_target,
                    edge.get("color", ""),
                    edge.get("thickness", ""),
                    edge.get("legend_code", ""),
                    edge.get("notes", ""),
                    record.source.name,
                ]
            )
            counts["matrix_edges"] += 1

    write_csv(
        OUTPUT_DIR / "ingredients.csv",
        ["ingredient", "page_reference", "summary", "additional_notes", "uncertainties", "source_file"],
        ingredient_rows,
    )
    write_csv(
        OUTPUT_DIR / "pairings.csv",
        ["ingredient", "target", "tier", "source"],
        pairing_rows,
    )
    write_csv(
        OUTPUT_DIR / "substitutes.csv",
        ["ingredient", "substitute", "source_file"],
        substitute_rows,
    )
    write_csv(
        OUTPUT_DIR / "matrix_nodes.csv",
        ["ingredient", "label", "color", "relative_size", "legend_code", "notes", "source_file"],
        node_rows,
    )
    write_csv(
        OUTPUT_DIR / "matrix_edges.csv",
        ["ingredient", "source", "target", "color", "thickness", "legend_code", "notes", "source_file"],
        edge_rows,
    )

    return counts


def _iter_pairings(
    ingredient: str, best: Optional[Sequence[Any]], surprise: Optional[Sequence[Any]]
) -> Iterable[Dict[str, str]]:
    for item in best or []:
        yield {
            "target": str(item),
            "tier": "best",
            "source": "best_pairings",
        }
    for item in surprise or []:
        yield {
            "target": str(item),
            "tier": "surprise",
            "source": "surprise_pairings",
        }


def write_report(counts: Dict[str, int], warnings: Sequence[str]) -> None:
    ensure_output_dir(OUTPUT_DIR)
    report_path = OUTPUT_DIR / "report.txt"
    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"Flavor Matrix processing report ({datetime.utcnow().isoformat()}Z)\n")
        f.write("-" * 60 + "\n")
        for key in sorted(counts):
            f.write(f"{key}: {counts[key]}\n")
        f.write("\nWarnings:\n")
        if warnings:
            for warn in warnings:
                f.write(f"- {warn}\n")
        else:
            f.write("None\n")


def main() -> None:
    input_path = INPUT_DIR
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])

    try:
        records = load_records(input_path)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[ERROR] Failed to load records: {exc}", file=sys.stderr)
        sys.exit(1)

    if not records:
        print(f"[WARN] No JSON records found in {input_path}", file=sys.stderr)
        sys.exit(0)

    warnings: List[str] = []
    for record in records:
        warnings.extend(validate_record(record))

    counts = build_outputs(records)
    write_report(counts, warnings)

    print(f"Processed {len(records)} ingredient entries from {input_path}")
    if warnings:
        print(f"Warnings were recorded. See {OUTPUT_DIR / 'report.txt'} for details.")
    else:
        print("No validation warnings.")


if __name__ == "__main__":
    main()
