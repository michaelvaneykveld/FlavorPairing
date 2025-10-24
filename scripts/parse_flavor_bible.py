"""Extract ingredient entries from *The Flavor Bible* into structured JSON."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
TEXT_DIR = ROOT / "docs" / "extracted" / "flavor-bible" / "OEBPS" / "Text"
OUTPUT_PATH = ROOT / "docs" / "flavor-bible-processed" / "flavor-bible.json"
NS = {"x": "http://www.w3.org/1999/xhtml"}
CHAPTER_FILES = sorted(TEXT_DIR.glob("FlavorBible_chap-3*.html"), key=lambda p: p.name)

SKIP_KEYWORDS = {
    "CUISINE",
    "APPETIZER",
    "APPETIZERS",
    "AROMA",
    "AROMAS",
    "ACIDITY",
    "FLAVOR MATCHMAKING",
    "TECHNIQUES",
    "DISHES",
    "FLAVOR PAIRING",
    "AUTUMN",
    "WINTER",
    "SPRING",
    "SUMMER",
    "BREAKFAST",
    "BRUNCH",
    "LUNCH",
    "DINNER",
    "BITTERNESS",
    "UMAMI",
    "SWEETNESS",
    "SALTINESS",
    "FRESHNESS",
    "GENERAL",
    "MIXED",
    "DESSERT",
    "DESSERTS",
    "DRINKS",
    "SALADS",
    "SOUPS",
    "SAUCES",
    "SMOOTHIES",
    "SNACKS",
    "STOCK",
    "TRAIL MIX",
}

PAIRING_STOPWORDS = {
    "cuisine",
    "dessert",
    "desserts",
    "drink",
    "drinks",
    "smoothie",
    "smoothies",
    "juice",
    "juices",
    "cocktail",
    "cocktails",
    "soup",
    "soups",
    "salad",
    "salads",
    "sandwich",
    "sandwiches",
    "burrito",
    "burritos",
    "marinade",
    "marinades",
    "sauce",
    "sauces",
    "stock",
    "stocks",
    "broth",
    "dishes",
    "pudding",
    "puddings",
    "trail mix",
    "mix",
    "baked goods",
    "stuffing",
    "stuffings",
    "snack",
    "snacks",
}

TIER_PRIORITY = {"ethereal": 3, "classic": 2, "frequent": 1, "recommended": 0}


@dataclass
class Entry:
    heading: str
    content: List[ET.Element]
    source_path: Path


def strip_tag(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


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

    ascii_name = working
    ascii_name = re.sub(r"[^a-zA-Z0-9 '\-]", " ", ascii_name)
    ascii_name = re.sub(r"\s+", " ", ascii_name).strip(" ,;- ")
    if not ascii_name:
        return None, original

    canonical = ascii_name.lower()
    return canonical, original


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def load_body_elements(path: Path) -> List[ET.Element]:
    root = ET.parse(path).getroot()
    body = root.find(".//x:body", NS)
    if body is None:
        raise RuntimeError(f"Body not found in source {path}")
    return list(body)


def split_heading_parts(elem: ET.Element) -> List[str]:
    parts: List[str] = []
    current: List[str] = []

    def flush() -> None:
        if current:
            parts.append(clean_text("".join(current)))
            current.clear()

    if elem.text:
        current.append(elem.text)
    for child in list(elem):
        if child.tag == "{http://www.w3.org/1999/xhtml}br":
            flush()
        else:
            current.append("".join(child.itertext()))
        if child.tail:
            current.append(child.tail)
    flush()
    return [part for part in parts if part]


def iter_entries() -> Iterable[Entry]:
    for chapter_path in CHAPTER_FILES:
        elems = load_body_elements(chapter_path)
        heading: Optional[str] = None
        buffer: List[ET.Element] = []

        for elem in elems:
            klass = elem.get("class")
            if klass == "h":
                parts = split_heading_parts(elem)
                if heading is not None and not should_skip_heading(heading):
                    yield Entry(heading, buffer, chapter_path)
                for part in parts[:-1]:
                    if part and not should_skip_heading(part):
                        yield Entry(part, [], chapter_path)
                heading = parts[-1] if parts else ""
                buffer = []
            elif heading is not None:
                buffer.append(elem)

        if heading is not None and buffer and not should_skip_heading(heading):
            yield Entry(heading, buffer, chapter_path)


def should_skip_heading(heading: str) -> bool:
    upper = heading.upper()
    if any(keyword in upper for keyword in SKIP_KEYWORDS):
        return True
    if "IN GENERAL" in upper or "MIXED" in upper:
        return True
    if upper.startswith("SEE "):
        return True
    canonical, _ = canonicalize_name(heading)
    return canonical is None


def parse_entry(entry: Entry) -> Optional[Dict[str, object]]:
    canonical_name, _ = canonicalize_name(entry.heading)
    if not canonical_name:
        return None

    display_name = clean_text(entry.heading)
    display_name_ascii = "".join(
        ch for ch in unicodedata.normalize("NFKD", display_name) if not unicodedata.combining(ch)
    )
    display_name = re.sub(r"\s+", " ", display_name_ascii).strip()
    metadata = {
        "season": [],
        "taste": [],
        "weight": None,
        "volume": None,
        "techniques": [],
        "tips": [],
        "primary_function": None,
        "botanical_relatives": [],
        "possible_substitutes": [],
    }
    pairings: Dict[str, Dict[str, object]] = {}
    avoid: Dict[str, Dict[str, str]] = {}
    affinities: List[Dict[str, object]] = []
    notes: List[str] = []

    current_section = "pairings"

    for elem in entry.content:
        klass = elem.get("class")
        raw_text = "".join(elem.itertext())
        text = clean_text(raw_text)
        if not text:
            continue

        label, value = extract_label_and_value(elem, text)
        if label:
            handle_metadata(label, value, metadata, avoid, notes)
            continue

        if klass == "h2":
            if "flavor affinities" in text.lower():
                current_section = "affinities"
            else:
                current_section = "other"
            continue

        if current_section == "affinities" and klass == "bl1":
            affinity_items: List[str] = []
            for part in text.split("+"):
                canonical, _ = canonicalize_name(part)
                if not canonical or should_skip_pairing(canonical):
                    continue
                affinity_items.append(canonical)
            if len(affinity_items) >= 2:
                affinities.append({"items": affinity_items})
            continue

        if klass in {"bl1", "nl1", "nl"}:
            canonical, original = canonicalize_name(text)
            if not canonical or should_skip_pairing(canonical):
                continue
            tier = determine_tier(elem, text)
            existing = pairings.get(canonical)
            if existing is None or TIER_PRIORITY[tier] > TIER_PRIORITY[existing["tier"]]:
                pairings[canonical] = {"ingredient": canonical, "display_name": original, "tier": tier}

    compact_metadata(metadata)

    record = {
        "ingredient": canonical_name,
        "display_name": display_name,
        "slug": slugify(canonical_name),
    }
    if metadata:
        record["metadata"] = metadata
    if pairings:
        record["pairings"] = sorted(pairings.values(), key=lambda item: item["ingredient"])
    if avoid:
        record["avoid"] = sorted(avoid.keys())
    if affinities:
        record["flavor_affinities"] = affinities
    if notes:
        record["notes"] = notes

    return record


def extract_label_and_value(elem: ET.Element, text: str) -> Tuple[Optional[str], Optional[str]]:
    strong = elem.find(".//x:strong", NS)
    if strong is None:
        return None, None
    label_text = clean_text("".join(strong.itertext()))
    if not label_text.endswith(":"):
        return None, None
    label = label_text[:-1].strip().lower()
    if not label:
        return None, None
    value = text[len(label_text) :].strip()
    return label, value


def handle_metadata(
    label: str,
    value: str,
    metadata: Dict[str, object],
    avoid: Dict[str, Dict[str, str]],
    notes: List[str],
) -> None:
    list_labels = {
        "season": "season",
        "taste": "taste",
        "techniques": "techniques",
        "botanical relatives": "botanical_relatives",
        "possible substitutes": "possible_substitutes",
    }
    scalar_labels = {
        "weight": "weight",
        "volume": "volume",
        "primary function": "primary_function",
        "function": "primary_function",
    }

    if label in list_labels:
        metadata[list_labels[label]].extend(split_list(value))
        metadata[list_labels[label]] = dedupe(metadata[list_labels[label]])
    elif label in scalar_labels:
        metadata[scalar_labels[label]] = clean_text(value)
    elif label in {"tips", "tip"}:
        if value:
            metadata["tips"].append(clean_text(value))
    elif label == "avoid":
        for entry in split_list(value):
            canonical, original = canonicalize_name(entry)
            if canonical and not should_skip_pairing(canonical):
                avoid[canonical] = {"ingredient": canonical, "display_name": original}
    else:
        if value:
            notes.append(f"{label.title()}: {clean_text(value)}")


def determine_tier(elem: ET.Element, text: str) -> str:
    raw = "".join(elem.itertext())
    if "*" in raw or "*" in text:
        return "ethereal"
    strong_nodes = elem.findall(".//x:strong", NS)
    if strong_nodes:
        strong_text = "".join("".join(node.itertext()) for node in strong_nodes)
        letters = re.sub(r"[^A-Za-z]", "", strong_text)
        if letters and letters.isupper():
            return "classic"
        return "frequent"
    return "recommended"


def split_list(value: str) -> List[str]:
    tokens: List[str] = []
    current: List[str] = []
    depth = 0
    for char in value:
        if char in ",;" and depth == 0:
            token = clean_text("".join(current))
            if token:
                tokens.append(token)
            current = []
            continue
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        current.append(char)
    token = clean_text("".join(current))
    if token:
        tokens.append(token)
    return tokens or ([clean_text(value)] if value else [])


def should_skip_pairing(canonical: str) -> bool:
    if not canonical:
        return True
    lower = canonical.lower()
    for word in PAIRING_STOPWORDS:
        if word in lower:
            return True
    return False


def dedupe(items: List[str]) -> List[str]:
    seen = set()
    deduped = []
    for item in items:
        cleaned = clean_text(item)
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered not in seen:
            seen.add(lowered)
            deduped.append(lowered)
    return deduped


def compact_metadata(metadata: Dict[str, object]) -> None:
    for key in list(metadata.keys()):
        value = metadata[key]
        if isinstance(value, list):
            metadata[key] = [clean_text(item) for item in value if clean_text(item)]
        elif isinstance(value, str):
            metadata[key] = clean_text(value)
    for key in list(metadata.keys()):
        value = metadata[key]
        if value in (None, [], ""):
            metadata.pop(key)


def append_record(record: Dict[str, object]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists():
        data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    else:
        data = []

    if any(item.get("slug") == record["slug"] for item in data):
        return

    data.append(record)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse Flavor Bible ingredient entries.")
    parser.add_argument("--limit", type=int, default=5, help="Number of new entries to append (default: 5)")
    args = parser.parse_args()

    processed = 0
    existing = set()
    if OUTPUT_PATH.exists():
        existing = {item["slug"] for item in json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))}

    for entry in iter_entries():
        canonical_name, _ = canonicalize_name(entry.heading)
        if not canonical_name:
            continue
        slug = slugify(canonical_name)
        if slug in existing:
            continue
        record = parse_entry(entry)
        if record is None:
            continue
        append_record(record)
        existing.add(slug)
        processed += 1
        print(f"Captured ingredient: {record['display_name']}")
        if processed >= args.limit:
            break

    if processed == 0:
        print("No new entries processed.")


if __name__ == "__main__":
    main()
