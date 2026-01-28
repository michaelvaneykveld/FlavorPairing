"""Build a canonical ingredient registry from parsed book datasets."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = [
    ("flavor-bible", ROOT / "docs" / "flavor-bible-processed" / "flavor-bible.json"),
    ("vegetarian-flavor-bible", ROOT / "docs" / "vegetarian-flavor-bible-processed" / "vegetarian-flavor-bible.json"),
]
OUTPUT_DIR = ROOT / "docs" / "canonical-registry"
OUTPUT_REGISTRY = OUTPUT_DIR / "ingredient_registry.json"
OUTPUT_REPORT = OUTPUT_DIR / "ingredient_registry_report.json"

PLURAL_EXCEPTIONS = {
    "bass",
    "citrus",
    "mollasses",
    "molasses",
    "species",
    "series",
    "bison",
    "salmon",
    "trout",
    "couscous",
    "news",
    "greens",
}


@dataclass
class RegistryEntry:
    canonical: str
    slug: str
    display_names: Set[str] = field(default_factory=set)
    sources: Set[str] = field(default_factory=set)
    aliases: Set[str] = field(default_factory=set)


@dataclass
class SourceIngredient:
    source: str
    canonical: str
    display_name: str
    slug: str


def clean_text(text: Optional[str]) -> str:
    if text is None:
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\xa0", " ")
    normalized = normalized.replace("\u2013", "-")
    normalized = normalized.replace("\u2014", "-")
    normalized = normalized.replace("\ufffd", "")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def canonicalize_name(text: str) -> Tuple[Optional[str], str]:
    original = clean_text(text)
    if not original:
        return None, original

    working = re.sub(r"\([^)]*\)", "", original)
    working = re.sub(r";?\s*see also.*", "", working, flags=re.IGNORECASE)
    working = re.sub(r";?\s*aka.*", "", working, flags=re.IGNORECASE)
    working = re.sub(r",?\s*aka.*", "", working, flags=re.IGNORECASE)
    working = re.sub(r",?\s*and/or.*", "", working, flags=re.IGNORECASE)
    working = re.sub(r",?\s*including.*", "", working, flags=re.IGNORECASE)
    working = re.sub(r",?\s*with.*", "", working, flags=re.IGNORECASE)
    working = re.sub(r",?\s*e\.g\.,?.*", "", working, flags=re.IGNORECASE)
    working = re.sub(r"\b(in general|general|mixed)\b.*", "", working, flags=re.IGNORECASE)
    working = working.replace("/", " ")
    ascii_working = "".join(
        ch for ch in unicodedata.normalize("NFKD", working) if not unicodedata.combining(ch)
    )
    ascii_working = re.sub(r"\bas a [^,;]+", "", ascii_working, flags=re.IGNORECASE)
    ascii_working = re.sub(r"\bfor [^,;]+", "", ascii_working, flags=re.IGNORECASE)
    ascii_working = re.sub(r"[^A-Za-z0-9,\- ]", " ", ascii_working)
    ascii_working = re.sub(r"\s+", " ", ascii_working).strip(" ,;-")

    if not ascii_working:
        return None, original

    working = ascii_working

    if "," in working:
        parts = [p.strip() for p in working.split(",") if p.strip()]
        if len(parts) == 2:
            working = f"{parts[1]} {parts[0]}".strip()
        else:
            working = " ".join(parts)

    ascii_name = re.sub(r"[^a-zA-Z0-9 '\-]", " ", working)
    ascii_name = re.sub(r"\s+", " ", ascii_name).strip(" ,;- ")
    if not ascii_name:
        return None, original

    canonical = ascii_name.lower()
    return canonical, original


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def normalize_token(token: str) -> str:
    token = token.lower()
    if token in PLURAL_EXCEPTIONS:
        return token
    if len(token) <= 3:
        return token
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("es") and len(token) > 4 and not token.endswith("ses"):
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def normalized_key(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9 ]", " ", name.lower())
    name = re.sub(r"\s+", " ", name).strip()
    tokens = [normalize_token(token) for token in name.split(" ") if token]
    return " ".join(tokens)


def split_alias_tokens(text: str) -> List[str]:
    working = clean_text(text)
    if not working:
        return []
    working = re.sub(r"\bsee also\b", ",", working, flags=re.IGNORECASE)
    working = re.sub(r"\b(a\.?k\.?a\.?|aka)\b", ",", working, flags=re.IGNORECASE)
    working = working.replace("/", ",")
    tokens = []
    for chunk in re.split(r"[;,]", working):
        chunk = chunk.strip()
        if not chunk:
            continue
        chunk = re.sub(r"^(and|or)\s+", "", chunk, flags=re.IGNORECASE)
        if chunk:
            tokens.append(chunk)
    return tokens


def extract_aliases(display_name: str) -> List[str]:
    aliases: List[str] = []
    if not display_name:
        return aliases

    for segment in re.findall(r"\(([^)]*)\)", display_name):
        for token in split_alias_tokens(segment):
            canonical, _ = canonicalize_name(token)
            if canonical:
                aliases.append(canonical)

    if "see also" in display_name.lower() or "aka" in display_name.lower():
        tail = display_name
        for token in split_alias_tokens(tail):
            canonical, _ = canonicalize_name(token)
            if canonical:
                aliases.append(canonical)

    return sorted(set(aliases))


def load_sources() -> List[SourceIngredient]:
    items: List[SourceIngredient] = []
    for source_name, path in SOURCE_FILES:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data:
            canonical = clean_text(entry.get("ingredient", ""))
            display_name = clean_text(entry.get("display_name", ""))
            slug = clean_text(entry.get("slug", ""))
            if not canonical or not slug:
                continue
            items.append(SourceIngredient(source=source_name, canonical=canonical, display_name=display_name, slug=slug))
    return items


def build_registry(items: Iterable[SourceIngredient]) -> Tuple[Dict[str, RegistryEntry], Dict[str, List[str]]]:
    registry: Dict[str, RegistryEntry] = {}
    alias_index: Dict[str, List[str]] = {}

    for item in items:
        entry = registry.get(item.canonical)
        if entry is None:
            entry = RegistryEntry(canonical=item.canonical, slug=slugify(item.canonical))
            registry[item.canonical] = entry
        entry.display_names.add(item.display_name)
        entry.sources.add(item.source)

        for alias in extract_aliases(item.display_name):
            if alias == item.canonical:
                continue
            entry.aliases.add(alias)
            alias_index.setdefault(alias, []).append(item.canonical)

    return registry, alias_index


def summarize_conflicts(registry: Dict[str, RegistryEntry], alias_index: Dict[str, List[str]]) -> Dict[str, object]:
    normalized_map: Dict[str, List[str]] = {}
    for canonical in registry:
        key = normalized_key(canonical)
        normalized_map.setdefault(key, []).append(canonical)

    collisions = {key: sorted(values) for key, values in normalized_map.items() if len(values) > 1}
    alias_collisions = {
        alias: sorted(set(canonicals))
        for alias, canonicals in alias_index.items()
        if len(set(canonicals)) > 1
    }

    alias_matches = {
        alias: sorted(set(canonicals))
        for alias, canonicals in alias_index.items()
        if alias in registry and alias not in canonicals
    }

    return {
        "normalized_collisions": collisions,
        "alias_collisions": alias_collisions,
        "alias_matches_existing_canonical": alias_matches,
    }


def write_outputs(registry: Dict[str, RegistryEntry], conflicts: Dict[str, object]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    registry_payload = [
        {
            "canonical": entry.canonical,
            "slug": entry.slug,
            "display_names": sorted(entry.display_names),
            "sources": sorted(entry.sources),
            "aliases": sorted(entry.aliases),
            "normalized_key": normalized_key(entry.canonical),
        }
        for entry in sorted(registry.values(), key=lambda e: e.canonical)
    ]

    OUTPUT_REGISTRY.write_text(json.dumps(registry_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    report = {
        "total_canonicals": len(registry_payload),
        "alias_total": sum(len(entry["aliases"]) for entry in registry_payload),
        "conflicts": conflicts,
    }
    OUTPUT_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    items = load_sources()
    registry, alias_index = build_registry(items)
    conflicts = summarize_conflicts(registry, alias_index)
    write_outputs(registry, conflicts)
    print(f"Registry entries: {len(registry)}")
    print(f"Report written: {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
