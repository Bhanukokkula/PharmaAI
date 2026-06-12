"""Real OTC product ingestion from the openFDA drug label API.

Pulls HUMAN OTC DRUG labels, maps each into one of our 5 storefront
categories using keyword rules over `purpose` / `indications_and_usage` /
`active_ingredient`, dedupes on (generic_name, brand_name) keeping the most
recent label by `effective_time`, and writes the cleaned catalog to
ml/data/products.json for seed.py to load.

Raw API pages are cached to disk (ml/data/openfda_cache/) so re-runs don't
re-hit the API.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
from pathlib import Path

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OPENFDA_URL = "https://api.fda.gov/drug/label.json"
SEARCH_QUERY = 'openfda.product_type:"HUMAN OTC DRUG"'
PAGE_SIZE = 1000
MAX_PAGES = 25  # safety cap: up to 25,000 raw records scanned

DATA_DIR = Path(__file__).resolve().parent / "data"
CACHE_DIR = DATA_DIR / "openfda_cache"
OUTPUT_PATH = DATA_DIR / "products.json"

CATEGORIES = [
    "Pain Relief",
    "Allergy",
    "Cold & Flu",
    "Digestive",
    "Vitamins & Supplements",
]

# Per-category SKU targets. Real openFDA drug-label data is "HUMAN OTC DRUG"
# labels and barely covers dietary supplements (those are regulated
# separately from "drugs") -- every supplement-shaped match we found in 25k
# scanned records was a low-quality/scam listing (e.g. "NAD Plus Patch",
# "Gout Relief"). So Vitamins & Supplements takes 0 from openFDA; the entire
# category comes from the hand-curated ml/data/curated_supplements.json
# (documented in its own header). The other four categories land at 45 each,
# for ~200 total with the 20 curated supplements.
TARGET_PER_CATEGORY = {
    "Pain Relief": 45,
    "Allergy": 45,
    "Cold & Flu": 45,
    "Digestive": 45,
    "Vitamins & Supplements": 0,
}

# Keyword rules over (purpose + indications_and_usage + active_ingredient),
# lowercased. A product's category is whichever list has the most keyword
# hits; CATEGORY_PRIORITY breaks ties.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Cold & Flu": [
        "common cold",
        "cold symptoms",
        "flu",
        "influenza",
        "cough",
        "antitussive",
        "expectorant",
        "decongestant",
        "nasal congestion",
        "chest congestion",
        "sore throat",
        "guaifenesin",
        "dextromethorphan",
        "pseudoephedrine",
        "phenylephrine",
    ],
    "Allergy": [
        "antihistamine",
        "allergy",
        "allergies",
        "hay fever",
        "allergic rhinitis",
        "runny nose",
        "itchy",
        "watery eyes",
        "sneezing",
        "loratadine",
        "cetirizine",
        "fexofenadine",
        "chlorpheniramine",
    ],
    "Digestive": [
        "antacid",
        "heartburn",
        "acid reducer",
        "acid indigestion",
        "laxative",
        "antidiarrheal",
        "diarrhea",
        "upset stomach",
        "indigestion",
        "constipation",
        "stool softener",
        "antiemetic",
        "nausea",
        "bloating",
        "anti-gas",
        "simethicone",
        "loperamide",
        "famotidine",
        "omeprazole",
        "bismuth subsalicylate",
        "laxatives",
    ],
    "Pain Relief": [
        "pain reliever",
        "fever reducer",
        "analgesic",
        "antipyretic",
        "headache",
        "muscle ache",
        "minor arthritis pain",
        "back ache",
        "backache",
        "toothache",
        "menstrual cramps",
        "acetaminophen",
        "ibuprofen",
        "naproxen sodium",
        "aspirin",
        "topical analgesic",
    ],
    "Vitamins & Supplements": [
        "dietary supplement",
        "multivitamin",
        "multi-vitamin",
        "multi-mineral",
        "mineral supplement",
        "nutritional supplement",
        "vitamin a",
        "vitamin c",
        "vitamin d",
        "vitamin e",
        "vitamin b12",
        "vitamin b6",
        "vitamin b-complex",
        "folic acid",
        "ferrous sulfate",
        "ferrous fumarate",
        "iron supplement",
        "iron deficiency",
        "zinc gluconate",
        "zinc supplement",
        "niacin",
        "thiamine",
        "riboflavin",
        "glucosamine",
        "chondroitin",
        "omega-3",
        "fish oil",
        "probiotic",
        "prenatal",
        "calcium supplement",
    ],
}

# Tie-break order when multiple categories score equally.
CATEGORY_PRIORITY = [
    "Cold & Flu",
    "Allergy",
    "Digestive",
    "Pain Relief",
    "Vitamins & Supplements",
]

# Hard exclusions checked against purpose/indications/active_ingredient/
# warnings/spl_unclassified_section. These catch labels that are technically
# "HUMAN OTC DRUG" but aren't storefront-appropriate: homeopathic remedies
# (no accepted clinical evidence behind the label claims) and cosmetic/
# first-aid products that would otherwise false-match on incidental
# ingredient mentions (e.g. a hand sanitizer's "with Vitamin E" tagline).
EXCLUDE_KEYWORDS = [
    "homeopathic",
    "homeopathy",
    "according to standard homeopathic",
    "hpus",
    "hemorrhoid",
    "anorectal",
    "hand sanitizer",
    "anti-aging",
    "antiaging",
    "anti aging",
    "wrinkle",
    "hair growth",
    "hair loss",
    "minoxidil",
    "skin whitening",
    "skin lightening",
    "sunscreen",
    # Scam/low-quality "supplement" listings that otherwise slip into
    # Vitamins & Supplements via incidental vitamin/mineral mentions.
    "corpus cavernosum",
    "sexual life",
    "erectile",
    "kidney repair",
    "gout relief",
    "stye",
    "nail treatment",
    "petroleum jelly",
    "miracle balm",
    "nad plus",
    "oyster peptide",
]

# Homeopathic potency notation (e.g. "30X", "6C", "200C"). Two or more
# matches in a label's text is a strong homeopathic signal even when the
# word "homeopathic" itself isn't present.
_POTENCY_RE = re.compile(r"\b\d{1,4}\s?[xck]\b", re.IGNORECASE)

_SECTION_HEADER_RE = re.compile(
    r"^(purposes?|uses?|warnings?|directions?|active ingredients?\(?s?\)?|"
    r"drug facts|other information|indications( and usage)?)\s*[:.]?\s*",
    re.IGNORECASE,
)


def _first(value):
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _clean_text(text: str | None) -> str | None:
    """Light cleanup: collapse whitespace, strip a leading section header."""
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    text = _SECTION_HEADER_RE.sub("", text, count=1).strip()
    return text or None


def is_excluded(text: str) -> bool:
    text = text.lower()
    if any(kw in text for kw in EXCLUDE_KEYWORDS):
        return True
    return len(_POTENCY_RE.findall(text)) >= 2


def categorize(text: str) -> str | None:
    text = text.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", text))
        if score:
            scores[category] = score

    if not scores:
        return None

    best = max(scores.values())
    candidates = [c for c, s in scores.items() if s == best]
    if len(candidates) == 1:
        return candidates[0]
    for c in CATEGORY_PRIORITY:
        if c in candidates:
            return c
    return candidates[0]


def fetch_page(client: httpx.Client, skip: int, api_key: str | None) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"page_skip{skip}_limit{PAGE_SIZE}.json"
    if cache_file.exists():
        log.info("Using cached page skip=%d", skip)
        return json.loads(cache_file.read_text())

    params = {"search": SEARCH_QUERY, "limit": PAGE_SIZE, "skip": skip}
    if api_key:
        params["api_key"] = api_key

    for attempt in range(5):
        resp = client.get(OPENFDA_URL, params=params, timeout=60)
        if resp.status_code == 429:
            wait = 2**attempt
            log.warning("Rate limited (attempt %d), sleeping %ds", attempt + 1, wait)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        data = resp.json()
        cache_file.write_text(json.dumps(data))
        return data

    raise RuntimeError(f"Failed to fetch page skip={skip} after retries")


def extract_product(result: dict) -> dict | None:
    openfda = result.get("openfda", {})
    brand_name = _first(openfda.get("brand_name"))
    generic_name = _first(openfda.get("generic_name"))

    if not brand_name and not generic_name:
        return None

    purpose_raw = _first(result.get("purpose"))
    indications_raw = _first(result.get("indications_and_usage"))
    active_ingredient_raw = _first(result.get("active_ingredient"))
    warnings_raw = _first(result.get("warnings"))
    unclassified_raw = _first(result.get("spl_unclassified_section"))

    exclusion_text = " ".join(
        filter(
            None,
            [purpose_raw, indications_raw, active_ingredient_raw, warnings_raw, unclassified_raw],
        )
    )
    if is_excluded(exclusion_text):
        return None

    category_text = " ".join(
        filter(None, [purpose_raw, indications_raw, active_ingredient_raw])
    )
    category = categorize(category_text)
    if category is None:
        return None

    dedup_key = "{}|{}".format(
        (generic_name or "").strip().upper(), (brand_name or "").strip().upper()
    )

    return {
        "brand_name": brand_name or generic_name,
        "generic_name": generic_name,
        "category": category,
        "purpose": _clean_text(purpose_raw) or _clean_text(indications_raw),
        "active_ingredient": _clean_text(active_ingredient_raw),
        "warnings": _clean_text(_first(result.get("warnings"))),
        "dosage_and_administration": _clean_text(
            _first(result.get("dosage_and_administration"))
        ),
        "route": _first(openfda.get("route")),
        "product_ndc": _first(openfda.get("product_ndc")),
        "rxcui": _first(openfda.get("rxcui")),
        "effective_time": result.get("effective_time") or "",
        "dedup_key": dedup_key,
    }


def run(
    target_per_category: dict[str, int] = TARGET_PER_CATEGORY,
    max_pages: int = MAX_PAGES,
    api_key: str | None = None,
) -> list[dict]:
    best: dict[str, dict] = {}  # dedup_key -> product (most recent effective_time wins)

    with httpx.Client() as client:
        for page in range(max_pages):
            skip = page * PAGE_SIZE
            data = fetch_page(client, skip, api_key)
            results = data.get("results", [])
            if not results:
                log.info("No more results at skip=%d, stopping", skip)
                break

            for result in results:
                product = extract_product(result)
                if product is None:
                    continue
                key = product["dedup_key"]
                existing = best.get(key)
                if existing is None or product["effective_time"] > existing["effective_time"]:
                    best[key] = product

            counts = {c: 0 for c in CATEGORIES}
            for p in best.values():
                counts[p["category"]] += 1
            log.info("After page %d (skip=%d): %s", page, skip, counts)

            if all(counts[c] >= target_per_category[c] for c in CATEGORIES):
                log.info("Reached target for all categories, stopping")
                break

            if not api_key:
                time.sleep(0.2)  # be polite without an API key

    by_category: dict[str, list[dict]] = {c: [] for c in CATEGORIES}
    for p in best.values():
        by_category[p["category"]].append(p)

    products: list[dict] = []
    for c in CATEGORIES:
        items = sorted(by_category[c], key=lambda p: p["brand_name"] or "")
        cap = target_per_category[c]
        kept = items[:cap]
        log.info("%s: %d candidates, keeping %d", c, len(items), len(kept))
        products.extend(kept)

    for p in products:
        del p["dedup_key"]
        del p["effective_time"]

    return products


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest OTC products from openFDA")
    parser.add_argument("--max-pages", type=int, default=MAX_PAGES)
    parser.add_argument("--api-key", type=str, default=None)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    products = run(max_pages=args.max_pages, api_key=args.api_key)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(products, indent=2))
    log.info("Wrote %d products to %s", len(products), args.output)


if __name__ == "__main__":
    main()
