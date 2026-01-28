"""Extract ingredient entries from *The Vegetarian Flavor Bible* into JSON."""

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
TEXT_DIR = ROOT / "docs" / "extracted" / "vegetarian-flavor-bible" / "OEBPS"
OUTPUT_PATH = ROOT / "docs" / "vegetarian-flavor-bible-processed" / "vegetarian-flavor-bible.json"
NS = {"x": "http://www.w3.org/1999/xhtml"}
XHTML_FILES = sorted(
    path for path in TEXT_DIR.glob("*.xhtml") if path.name.startswith(("chapter003", "chapter004", "A-Z"))
)

SKIP_KEYWORDS = {
    "CUISINE",
    "APPETIZER",
    "APPETIZERS",
    "AROMA",
    "AROMAS",
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
    "SOUP",
    "SAUCES",
    "SMOOTHIES",
    "SNACKS",
    "STOCK",
    "TRAIL MIX",
    "BALANCE",
    "COOLING",
    "WARMING",
    "SOURNESS",
    "PIQUANCY",
    "LUXURIOUS",
    "MENU",
    "CHRISTMAS",
    "THANKSGIVING",
    "PRESSURE-COOKING",
    "SOUS-VIDE",
    "SOUS-VIDE COOKING",
    "SLOW-COOKED",
    "SMOKING",
    "GRILLING",
    "DEHYDRATING",
    "THICKENING AGENTS",
    "OIL SUBSTITUTES",
    "ORGANIC PRODUCE",
    "WHOLE FOODS",
    "WHOLE GRAINS",
    "GLUTEN",
    "GLUTEN-FREE",
    "FRUIT",
    "FRUITS",
    "VEGETABLE",
    "VEGETABLES",
    "MEAT",
    "MEATS",
    "SEAFOOD",
    "SHELLFISH",
    "POULTRY",
    "SPICES",
    "HERBS",
    "GRAINS",
    "MACARONI AND CHEESE",
    "SALAD DRESSINGS",
    "VEGGIE BURGERS",
    "VEGETARIAN SUSHI",
    "SUSHI, VEGETARIAN",
    "PIECRUSTS",
    "POPCORN",
    "VITAMIX",
    "SOUTHWESTERN",
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
    "foods",
    "flavors",
    "dishes",
    "fruit",
    "fruits",
    "vegetable",
    "vegetables",
    "meat",
    "meats",
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


def split_heading_variants(heading: str) -> List[str]:
    text = clean_text(heading)
    if not text:
        return []
    split_points = [match.start() + 1 for match in re.finditer(r"\)\s+(?=[A-Z])", text)]
    if not split_points:
        return split_heading_compounds(text)
    parts: List[str] = []
    last = 0
    for point in split_points:
        parts.append(text[last:point].strip())
        last = point + 1
    parts.append(text[last:].strip())
    expanded: List[str] = []
    for part in parts:
        expanded.extend(split_heading_compounds(part))
    return [part for part in expanded if part]


def base_word(text: str) -> str:
    tokens = re.sub(r"[^A-Za-z]", " ", text).split()
    if not tokens:
        return ""
    word = tokens[0].lower()
    if len(word) > 3 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith(("ses", "xes", "zes", "ches", "shes", "oes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s"):
        return word[:-1]
    return word


def split_heading_compounds(text: str) -> List[str]:
    lowered = text.lower()
    if " and " in lowered:
        match = re.match(r"^(?P<base>[A-Za-z][A-Za-z '\-]+)\s+and\s+(?P=base)\s+(?P<suffix>.+)$", text, re.IGNORECASE)
        if match:
            base = clean_text(match.group("base"))
            suffix = clean_text(match.group("suffix"))
            return [base, f"{base} {suffix}".strip()]

    if "," in text:
        items = split_list(text)
        expanded: List[str] = []
        for item in items:
            item = re.sub(r"^(and|or)\s+", "", item.strip(), flags=re.IGNORECASE)
            if " and " in item.lower() and "(" not in item and ")" not in item:
                index = item.lower().find(" and ")
                left = item[:index]
                right = item[index + 5 :]
                expanded.extend([left, right])
            else:
                expanded.append(item)

        if expanded:
            base = base_word(expanded[0])
            if base and all(base_word(item) == base for item in expanded[1:]):
                return [clean_text(item) for item in expanded if clean_text(item)]

    return [text]


def iter_entries() -> Iterable[Entry]:
    for path in XHTML_FILES:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        body = root.find(".//x:body", NS)
        if body is None:
            continue

        heading: Optional[str] = None
        buffer: List[ET.Element] = []

        for elem in body.iter():
            tag = strip_tag(elem.tag)
            if tag == "h1" and elem.get("class") == "recipe-title":
                if heading is not None and buffer:
                    for index, part in enumerate(split_heading_variants(heading)):
                        if part and not should_skip_heading(part):
                            yield Entry(part, buffer if index == 0 else [], path)
                heading = "".join(elem.itertext())
                buffer = []
            elif heading is not None:
                buffer.append(elem)

        if heading is not None and buffer:
            for index, part in enumerate(split_heading_variants(heading)):
                if part and not should_skip_heading(part):
                    yield Entry(part, buffer if index == 0 else [], path)


def should_skip_heading(heading: str) -> bool:
    upper = heading.upper()
    if any(keyword in upper for keyword in SKIP_KEYWORDS):
        return True
    if "IN GENERAL" in upper or "MIXED" in upper:
        return True
    if upper.startswith("SEE "):
        return True
    canonical, _ = canonicalize_name(heading)
    if canonical is None:
        return True
    if len(canonical.strip()) <= 1:
        return True
    return False


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
        tag = strip_tag(elem.tag)
        cls = elem.get("class") or ""
        raw_text = "".join(elem.itertext())
        text = clean_text(raw_text)
        if not text:
            continue

        if tag == "p" and cls == "ingredient":
            if current_section == "affinities":
                affinity_items: List[str] = []
                for part in text.split("+"):
                    canonical, _ = canonicalize_name(part)
                    if not canonical or should_skip_pairing(canonical, part):
                        continue
                    affinity_items.append(canonical)
                if len(affinity_items) >= 2:
                    affinities.append({"items": affinity_items})
            else:
                tier = determine_tier(elem, text)
                for candidate in split_pairing_candidates(text):
                    canonical, original = canonicalize_name(candidate)
                    if not canonical or should_skip_pairing(canonical, candidate):
                        continue
                    existing = pairings.get(canonical)
                    if existing is None or TIER_PRIORITY[tier] > TIER_PRIORITY[existing["tier"]]:
                        pairings[canonical] = {"ingredient": canonical, "display_name": original, "tier": tier}
            continue

        label, value = extract_label_and_value(elem, text)
        if label:
            handle_metadata(label, value, metadata, avoid, notes)
            continue

        if tag == "h1" and cls == "ingredients-title":
            if "flavor affinities" in text.lower():
                current_section = "affinities"
            else:
                current_section = "other"
            continue

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
        "flavor": "taste",
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


def split_on_delimiter(text: str, delimiter: str) -> List[str]:
    lowered = text.lower()
    tokens: List[str] = []
    current: List[str] = []
    depth = 0
    i = 0
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")" and depth > 0:
            depth -= 1

        if depth == 0 and lowered.startswith(delimiter, i):
            token = clean_text("".join(current))
            if token:
                tokens.append(token)
            current = []
            i += len(delimiter)
            continue

        current.append(text[i])
        i += 1

    token = clean_text("".join(current))
    if token:
        tokens.append(token)
    return tokens if len(tokens) > 1 else [text]


def split_pairing_candidates(text: str) -> List[str]:
    candidates = [clean_text(text)]
    for delimiter in [" and ", " or ", " & ", "/"]:
        expanded: List[str] = []
        for candidate in candidates:
            expanded.extend(split_on_delimiter(candidate, delimiter))
        candidates = expanded
    return [candidate for candidate in candidates if candidate]


def should_skip_pairing(canonical: str, raw_text: Optional[str] = None) -> bool:
    if not canonical or len(canonical.strip()) <= 1:
        return True
    lower = canonical.lower()
    for word in PAIRING_STOPWORDS:
        if word in lower:
            return True
    if raw_text:
        raw_lower = raw_text.lower()
        if re.search(
            r"\b(add|avoid|bake|cook|fry|grill|mix|pair|pairs|pairing|roast|saute|sauté|serve|sprinkle|stir|try|use|using|goes|never)\b",
            raw_lower,
        ):
            return True
        if "a little " in raw_lower or "goes a very long way" in raw_lower:
            return True
        if len(raw_lower.split()) > 7:
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
    parser = argparse.ArgumentParser(description="Parse Vegetarian Flavor Bible entries.")
    parser.add_argument("--limit", type=int, default=50, help="Number of new entries to append (default: 50)")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild output from scratch")
    args = parser.parse_args()

    if args.rebuild and OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()

    processed = 0
    existing = set()
    if OUTPUT_PATH.exists():
        existing = {item["slug"] for item in json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))}

    limit = args.limit
    if args.rebuild:
        limit = 10**9

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
        if processed >= limit:
            break

    if processed == 0:
        print("No new entries processed.")


if __name__ == "__main__":
    main()
