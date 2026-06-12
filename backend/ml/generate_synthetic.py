"""Synthetic users + interaction events with planted segment ground truth.

Generates ~2,000 users, each assigned one of 6 hidden segments with a
category-affinity distribution. For every user we then synthesize
view/purchase/rating interaction events that reflect that affinity, with
some cross-segment noise and seasonality (e.g. allergy products spike in
spring, cold/flu products spike in winter).

`User.segment` is ground truth used only to *evaluate* the recommender in
train.py (precision@k against planted affinity) -- the recommender itself
never sees it.

Writes:
  - ml/data/users.json          one row per synthetic user
  - ml/data/interactions.json   view/purchase/rating events
  - ml/data/synthetic_report.txt counts, segment distribution, sanity check
  - ml/data/segment_category_heatmap.png  observed category share x segment

`product_index` in interactions.json is a 0-based index into
ml.catalog.load_catalog() -- see that module's docstring for why ordering
matters to seed.py.
"""

from __future__ import annotations

import argparse
import calendar
import json
import logging
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ml.catalog import CATEGORIES, load_catalog

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_OUTPUT = DATA_DIR / "users.json"
INTERACTIONS_OUTPUT = DATA_DIR / "interactions.json"
REPORT_OUTPUT = DATA_DIR / "synthetic_report.txt"
HEATMAP_OUTPUT = DATA_DIR / "segment_category_heatmap.png"

N_USERS = 2000
SEED = 42

# Fraction of interactions that ignore the user's segment affinity entirely
# and pick a uniformly random category -- cross-segment noise so the
# recommender problem isn't trivially separable.
NOISE_RATE = 0.12

# Multiplier applied to a category's affinity weight when the interaction
# falls in that category's "in season" months (see SEGMENTS below).
SEASON_BOOST = 2.5

# Extra weight added to a calendar month for every category that's "in
# season" during that month, before picking when an interaction happens.
MONTH_BOOST = 1.5

# 6 hidden segments. `weight` is the (approximate) share of the 2,000 users;
# `affinity` is each segment's category-interaction probability (sums to 1);
# `season_months` maps a category to the 1-12 calendar months it spikes in;
# `sessions_range` is how many "product interest" events a user generates;
# `purchase_rate`/`rating_rate` drive the view -> purchase -> rating funnel.
SEGMENTS: dict[str, dict] = {
    "Allergy-season buyer": {
        "weight": 0.18,
        "affinity": {
            "Allergy": 0.50,
            "Cold & Flu": 0.15,
            "Pain Relief": 0.10,
            "Digestive": 0.05,
            "Vitamins & Supplements": 0.20,
        },
        "season_months": {"Allergy": [3, 4, 5, 6]},
        "sessions_range": (15, 40),
        "purchase_rate": 0.35,
        "rating_rate": 0.35,
    },
    "Chronic vitamin reorderer": {
        "weight": 0.15,
        "affinity": {
            "Vitamins & Supplements": 0.60,
            "Digestive": 0.15,
            "Pain Relief": 0.10,
            "Allergy": 0.05,
            "Cold & Flu": 0.10,
        },
        "season_months": {},
        "sessions_range": (20, 50),
        "purchase_rate": 0.50,
        "rating_rate": 0.30,
    },
    "Cold/flu episodic": {
        "weight": 0.17,
        "affinity": {
            "Cold & Flu": 0.50,
            "Pain Relief": 0.20,
            "Allergy": 0.05,
            "Digestive": 0.05,
            "Vitamins & Supplements": 0.20,
        },
        "season_months": {"Cold & Flu": [11, 12, 1, 2]},
        "sessions_range": (10, 35),
        "purchase_rate": 0.40,
        "rating_rate": 0.30,
    },
    "Pain management regular": {
        "weight": 0.15,
        "affinity": {
            "Pain Relief": 0.55,
            "Digestive": 0.15,
            "Vitamins & Supplements": 0.10,
            "Cold & Flu": 0.10,
            "Allergy": 0.10,
        },
        "season_months": {},
        "sessions_range": (20, 50),
        "purchase_rate": 0.45,
        "rating_rate": 0.30,
    },
    "Digestive-health buyer": {
        "weight": 0.15,
        "affinity": {
            "Digestive": 0.55,
            "Vitamins & Supplements": 0.20,
            "Pain Relief": 0.10,
            "Cold & Flu": 0.10,
            "Allergy": 0.05,
        },
        "season_months": {},
        "sessions_range": (15, 40),
        "purchase_rate": 0.40,
        "rating_rate": 0.30,
    },
    "Explorer/one-off": {
        "weight": 0.20,
        "affinity": {c: 0.20 for c in CATEGORIES},
        "season_months": {},
        "sessions_range": (3, 12),
        "purchase_rate": 0.15,
        "rating_rate": 0.20,
    },
}

# Skewed positive, like most e-commerce ratings.
RATING_DIST = {1: 0.03, 2: 0.07, 3: 0.15, 4: 0.35, 5: 0.40}


def _month_weights(segment_cfg: dict) -> list[float]:
    """12-element weight list (Jan..Dec) for when this segment's events happen."""
    weights = [1.0] * 12
    for months in segment_cfg["season_months"].values():
        for m in months:
            weights[m - 1] += MONTH_BOOST
    return weights


def _date_for_month(calendar_month: int, now: datetime) -> datetime:
    """Random timestamp within `calendar_month`, in the most recent year that
    month occurred (today's month is capped at today's day, so nothing is
    generated in the future)."""
    year = now.year if calendar_month <= now.month else now.year - 1
    if calendar_month == now.month:
        max_day = now.day
    else:
        max_day = calendar.monthrange(year, calendar_month)[1]
    day = random.randint(1, max_day)
    return datetime(
        year,
        calendar_month,
        day,
        random.randint(0, 23),
        random.randint(0, 59),
        random.randint(0, 59),
        tzinfo=timezone.utc,
    )


def _pick_category(segment_cfg: dict, calendar_month: int) -> str:
    if random.random() < NOISE_RATE:
        return random.choice(CATEGORIES)

    weights = dict(segment_cfg["affinity"])
    for category, months in segment_cfg["season_months"].items():
        if calendar_month in months:
            weights[category] = weights.get(category, 0.0) * SEASON_BOOST

    categories = list(weights.keys())
    return random.choices(categories, weights=list(weights.values()), k=1)[0]


def _generate_user_interactions(
    username: str,
    segment_cfg: dict,
    products_by_category: dict[str, list[int]],
    now: datetime,
) -> list[dict]:
    interactions: list[dict] = []
    month_weights = _month_weights(segment_cfg)
    months = list(range(1, 13))

    n_sessions = random.randint(*segment_cfg["sessions_range"])
    for _ in range(n_sessions):
        calendar_month = random.choices(months, weights=month_weights, k=1)[0]
        view_ts = _date_for_month(calendar_month, now)
        category = _pick_category(segment_cfg, calendar_month)
        product_index = random.choice(products_by_category[category])

        interactions.append(
            {
                "username": username,
                "product_index": product_index,
                "interaction_type": "view",
                "rating_value": None,
                "quantity": None,
                "timestamp": view_ts.isoformat(),
            }
        )

        if random.random() < segment_cfg["purchase_rate"]:
            purchase_ts = min(
                view_ts + timedelta(days=random.randint(0, 3), hours=random.randint(0, 12)),
                now,
            )
            interactions.append(
                {
                    "username": username,
                    "product_index": product_index,
                    "interaction_type": "purchase",
                    "rating_value": None,
                    "quantity": random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0],
                    "timestamp": purchase_ts.isoformat(),
                }
            )

            if random.random() < segment_cfg["rating_rate"]:
                rating_ts = min(purchase_ts + timedelta(days=random.randint(1, 14)), now)
                rating_value = random.choices(
                    list(RATING_DIST.keys()), weights=list(RATING_DIST.values()), k=1
                )[0]
                interactions.append(
                    {
                        "username": username,
                        "product_index": product_index,
                        "interaction_type": "rating",
                        "rating_value": float(rating_value),
                        "quantity": None,
                        "timestamp": rating_ts.isoformat(),
                    }
                )

    return interactions


def run(n_users: int = N_USERS, seed: int = SEED) -> tuple[list[dict], list[dict]]:
    random.seed(seed)

    catalog = load_catalog()
    products_by_category: dict[str, list[int]] = defaultdict(list)
    for idx, product in enumerate(catalog):
        products_by_category[product["category"]].append(idx)
    for category in CATEGORIES:
        if not products_by_category[category]:
            raise RuntimeError(f"No products in category {category!r} -- run ml.seed's ingest step first")

    segment_names = list(SEGMENTS.keys())
    segment_weights = [SEGMENTS[s]["weight"] for s in segment_names]

    now = datetime.now(timezone.utc)

    users: list[dict] = []
    interactions: list[dict] = []
    for i in range(1, n_users + 1):
        segment = random.choices(segment_names, weights=segment_weights, k=1)[0]
        username = f"user_{i:04d}"
        users.append(
            {
                "username": username,
                "display_name": f"Shopper {i:04d}",
                "segment": segment,
            }
        )
        interactions.extend(
            _generate_user_interactions(username, SEGMENTS[segment], products_by_category, now)
        )

    return users, interactions


def build_report(users: list[dict], interactions: list[dict], catalog: list[dict]) -> tuple[str, np.ndarray]:
    segment_names = list(SEGMENTS.keys())
    n_users = len(users)

    segment_counts = Counter(u["segment"] for u in users)
    type_counts = Counter(i["interaction_type"] for i in interactions)

    username_to_segment = {u["username"]: u["segment"] for u in users}
    segment_category_counts: dict[str, Counter] = {s: Counter() for s in segment_names}
    for interaction in interactions:
        segment = username_to_segment[interaction["username"]]
        category = catalog[interaction["product_index"]]["category"]
        segment_category_counts[segment][category] += 1

    matrix = np.zeros((len(segment_names), len(CATEGORIES)))
    for i, segment in enumerate(segment_names):
        total = sum(segment_category_counts[segment].values()) or 1
        for j, category in enumerate(CATEGORIES):
            matrix[i, j] = segment_category_counts[segment][category] / total

    lines: list[str] = []
    lines.append("PharmaAI synthetic data report")
    lines.append("=" * 60)
    lines.append(f"Users: {n_users}")
    lines.append(f"Interactions: {len(interactions)}")
    for itype in ("view", "purchase", "rating"):
        lines.append(f"  {itype}: {type_counts.get(itype, 0)}")
    lines.append("")

    lines.append("Segment distribution:")
    for segment in segment_names:
        count = segment_counts.get(segment, 0)
        lines.append(f"  {segment:<28} {count:>5} ({count / n_users:.1%})")
    lines.append("")

    lines.append("Observed interaction share by category, per segment")
    lines.append("(planted affinity shown in parentheses -- sanity check that")
    lines.append("interactions actually reflect the planted segments):")
    lines.append("")
    header = f"  {'segment':<28}" + "".join(f"{c:>24}" for c in CATEGORIES)
    lines.append(header)
    for i, segment in enumerate(segment_names):
        row = f"  {segment:<28}"
        for j, category in enumerate(CATEGORIES):
            observed = matrix[i, j]
            planted = SEGMENTS[segment]["affinity"].get(category, 0.0)
            row += f"{observed:>8.0%} ({planted:>4.0%})".rjust(24)
        lines.append(row)

    return "\n".join(lines), matrix


def save_heatmap(matrix: np.ndarray, segment_names: list[str], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    im = ax.imshow(matrix, cmap="viridis", aspect="auto", vmin=0, vmax=matrix.max())

    ax.set_xticks(range(len(CATEGORIES)))
    ax.set_xticklabels(CATEGORIES, rotation=30, ha="right")
    ax.set_yticks(range(len(segment_names)))
    ax.set_yticklabels(segment_names)

    for i in range(len(segment_names)):
        for j in range(len(CATEGORIES)):
            value = matrix[i, j]
            color = "white" if value < matrix.max() / 2 else "black"
            ax.text(j, i, f"{value:.0%}", ha="center", va="center", color=color)

    ax.set_title("Observed interaction share by category x segment")
    fig.colorbar(im, ax=ax, label="share of user's interactions")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic users + interactions")
    parser.add_argument("--n-users", type=int, default=N_USERS)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    catalog = load_catalog()
    users, interactions = run(n_users=args.n_users, seed=args.seed)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USERS_OUTPUT.write_text(json.dumps(users, indent=2))
    INTERACTIONS_OUTPUT.write_text(json.dumps(interactions, indent=2))

    report, matrix = build_report(users, interactions, catalog)
    REPORT_OUTPUT.write_text(report)
    save_heatmap(matrix, list(SEGMENTS.keys()), HEATMAP_OUTPUT)

    log.info("Wrote %d users to %s", len(users), USERS_OUTPUT)
    log.info("Wrote %d interactions to %s", len(interactions), INTERACTIONS_OUTPUT)
    log.info("Wrote report to %s", REPORT_OUTPUT)
    log.info("Wrote heatmap to %s", HEATMAP_OUTPUT)
    print(report)


if __name__ == "__main__":
    main()
