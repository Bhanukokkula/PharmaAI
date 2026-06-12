# PharmaAI

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?logo=tailwindcss&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-ORM-003B57?logo=sqlite&logoColor=white)
![MLflow](https://img.shields.io/badge/MLflow-0194E2?logo=mlflow&logoColor=white)

A local-first OTC (over-the-counter) pharmacy e-commerce demo: a full
storefront (landing page, browse, cart, multi-step checkout) on top of a real
FastAPI + SQLite catalog seeded from openFDA, with a content-based
recommendation engine and a thin, honest MLOps spine — training, evaluation,
MLflow tracking, and prediction logging.

**This is v1 — a base to iterate on, not a finished product.**

## ✨ Highlights

- 🛒 **Full storefront** — landing page with hero/categories/recommendations,
  category browse with filters, product detail pages with real FDA
  purpose/warnings text, cart, and a 3-step checkout, all on real seeded data.
- 🧠 **Content-based recommender** — blends item-content similarity,
  co-occurrence ("frequently bought together"), and popularity, evaluated
  against hidden synthetic user segments.
- 📊 **Honest MLOps spine** — `python -m ml.train` logs params, metrics, and
  artifacts to a local MLflow registry; every `/recommend` call writes a
  `PredictionLog` row.
- 🔐 **Mock auth, no real accounts** — a sign-in page with one-click "shop as a
  sample customer" personas, held entirely in React state (no localStorage, no
  passwords, no JWTs).
- 💳 **No real payments** — checkout's payment step is styled but
  non-functional; "placing an order" writes through the existing cart API.
- ✅ **Tested** — 29 backend tests covering catalog browsing, cart/checkout,
  mock sessions, and recommender scoring.
- 🚀 **One-command run** — `./run.sh` seeds the database, trains the
  recommender, and starts both servers.

## Quick start

```bash
git clone <repo-url> pharmaai
cd pharmaai
./run.sh
```

Then open http://localhost:5173. The first run seeds the database from openFDA
+ synthetic data and trains the recommender (about a minute); subsequent runs
reuse `backend/pharmaai.db` and `backend/ml/artifacts/`. See
[Running it](#running-it) for step-by-step and Docker options.

## Table of contents

- [Scope & safety framing](#scope--safety-framing-read-this-first)
- [Storefront UI](#storefront-ui)
- [Mock login & user identity](#mock-login--user-identity)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Running it](#running-it)
- [Training the recommender](#training-the-recommender)
- [Running the tests](#running-the-tests)
- [Repo structure](#repo-structure)
- [What's NOT in v1](#whats-not-in-v1-by-design)
- [Roadmap / next versions](#roadmap--next-versions)

## Scope & safety framing (read this first)

- **OTC / wellness products only.** No prescription drugs are stocked or
  referenced.
- This site provides **product information and shopping**, not medical
  advice. Recommendations are framed as "popular with similar shoppers" /
  "frequently bought together" — never as a diagnosis, dosage suggestion, or
  clinical guidance.
- `purpose` and `warnings` text shown on product pages is reproduced
  verbatim from openFDA drug-label data for informational purposes only.
- There is **no real authentication** — see "Mock login & user identity"
  below.
- There is **no payment processing** — checkout's payment step is a styled,
  non-functional form; "placing an order" just writes a row via the existing
  cart/checkout API.
- Users, orders, and **prices are synthetic demo data** — prices are
  illustrative only (see the footer on every page).

## Storefront UI

The frontend (`frontend/src`) is a small e-commerce shell on top of the
existing API:

- **Home** (`/`) — hero with search, category tiles, a "Recommended for you"
  strip from `/recommend` (labeled "popular with shoppers like you"),
  featured products, a trust band, and a "how it works" section.
- **Shop** (`/shop`) — product grid with category/price/search filters,
  pagination, loading skeletons, and an empty state.
- **Product detail** (`/products/:id`) — brand/generic name, price, real
  `purpose`/`warnings`/dosage text from the API, a styled warnings panel, and
  a "you might also like" row from the recommender.
- **Cart** (`/cart`) and **Checkout** (`/checkout`) — editable line items,
  subtotal/shipping/total, and a 3-step checkout (Shipping → Payment →
  Review) with a step indicator, ending at an order-confirmation screen.
- **Account** (`/account`) — active mock user and order history (via the
  additive `GET /orders` endpoint).

## Mock login & user identity

There's **no real authentication, no passwords, and no
localStorage/sessionStorage** — the active user lives only in a React
`AuthContext` for the lifetime of the browser tab.

`generate_synthetic.py` seeds ~2,000 synthetic users, each with a hidden
ground-truth `segment` (e.g. "Allergy-season buyer") used to evaluate the
recommender. Before signing in, the app browses as the API's default seeded
user, so the cart and recommendations work immediately.

The **Sign in** page (`/login`) is a mock auth form:

- Any email/password is accepted — the password is ignored, and the email is
  hashed to pick one of the first 200 seeded users, so different emails feel
  like different "accounts" with no real signup.
- "Quick demo: shop as a sample customer" lists one seeded persona per
  synthetic segment (via the additive `GET /users/personas` endpoint) for
  one-click switching.

Once signed in, the chosen user id is sent as an `X-User-Id` header on every
API request (unchanged mechanism), so the cart, order history, and
`/recommend` all reflect that user. "Sign out" simply forgets the in-memory
user id and falls back to the default seeded user — nothing is persisted.

## Architecture

```
┌──────────────────┐        HTTP/JSON        ┌──────────────────────────┐
│  Vite + React +  │ ──────────────────────▶ │        FastAPI            │
│  Tailwind (SPA)   │ ◀────────────────────── │  ┌──────────────────────┐ │
│                   │   X-User-Id header      │  │ routes/               │ │
│  pages/           │   (mock session)        │  │  catalog, cart,       │ │
│   Home            │                          │  │  users, orders,       │ │
│   Catalog (/shop) │                          │  │  recommend            │ │
│   ProductDetail   │                          │  └──────────┬───────────┘ │
│   Login (mock)    │                          │             │             │
│   Cart / Checkout │                          │  ┌──────────▼───────────┐ │
│   Account         │                          │  │ services/recommender/ │ │
└──────────────────┘                          │  │  base.py (interface) │ │
                                                │  │  content_based.py    │ │
                                                │  │  features.py,        │ │
                                                │  │  artifacts.py        │ │
                                                │  └──────────┬───────────┘ │
                                                │             │             │
                                                │  ┌──────────▼───────────┐ │
                                                │  │ SQLAlchemy ORM → SQLite│ │
                                                │  │ Product, User,        │ │
                                                │  │ Interaction,          │ │
                                                │  │ PredictionLog, Cart,  │ │
                                                │  │ Order                 │ │
                                                │  └───────────────────────┘ │
                                                └──────────────────────────┘

ml/
 ingest_openfda.py  ──▶ real OTC products  ──┐
 generate_synthetic.py ──▶ users + interactions ├──▶ seed.py ──▶ SQLite
 train.py ──▶ writes ml/artifacts/ (loaded by content_based.py) and
              logs params/metrics/model to ./mlruns (MLflow file store)
```

**The fork-agnostic boundary:** `app/services/recommender/base.py` defines
`RecommenderService`. Routes and the frontend depend only on this interface
— never on `ContentBasedRecommender` directly. Swapping in a future
RAG/chatbot assistant or a drift-prone forecasting model is a one-line change
in `get_recommender()`.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | FastAPI (Python 3.11+) |
| Frontend | Vite + React + Tailwind + lucide-react icons |
| DB | SQLite via SQLAlchemy ORM (ORM-only, so a Postgres swap later is a connection-string change) |
| Model registry | MLflow, local file store (`./mlruns`) |
| Auth | None — mock login UI sets an `X-User-Id` header, held in React state only |

## Running it

### Option A — one command

```bash
./run.sh
```

This creates the backend virtualenv, installs dependencies, seeds the DB and
trains the recommender on first run (subsequent runs reuse `pharmaai.db` and
`ml/artifacts/`), then starts the API and frontend dev server together.
Visit http://localhost:5173. Ctrl+C stops both. Override ports with
`BACKEND_PORT` / `FRONTEND_PORT` env vars if 8000/5173 are taken.

### Option B — local, step by step (for development)

Backend:

```bash
cd backend
python3.11 -m venv .venv   # or any Python 3.11+
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The first request creates `backend/pharmaai.db` and all tables. To populate
it with real OTC products and synthetic users/interactions:

```bash
python -m ml.seed
```

Frontend (separate terminal):

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173. The API runs at http://127.0.0.1:8000
(interactive docs at `/docs`).

### Option C — Docker Compose

```bash
docker compose up --build
```

Frontend at http://localhost:5173, API at http://localhost:8000. SQLite
needs no separate service — this is provided for environment parity, not
because the DB needs it.

## Training the recommender

```bash
cd backend
python -m ml.train
```

This builds the v1 content-based recommender from the seeded DB:

- an item-item **content similarity** matrix (TF-IDF over product
  name/purpose/active ingredient + category)
- an item-item **co-occurrence** matrix ("frequently bought together",
  from purchase interactions)
- a **popularity** vector (purchase counts, normalized)

These are saved to `backend/ml/artifacts/` (gitignored — regenerate any
time with `python -m ml.train`), which `ContentBasedRecommender` loads at
startup. At request time, the three signals are blended based on each
user's own interaction history (no per-request retraining).

It also logs params, metrics, and the artifacts themselves to the local
MLflow file store (`./mlruns`), and registers a new version of the
`pharmaai-content-based` model. The metrics are intentionally honest about
what they can and can't show:

- `precision_at_k_segment_affinity` vs. `precision_at_k_random_baseline` —
  do top-k recommendations land in the categories that a user's *hidden*
  synthetic segment favors (the recommender never sees `segment`), compared
  to a random-recommendation baseline for the same categories?
- `category_recall_at_k` / `item_recall_at_k` — leave-one-out: hide each
  user's most recent purchase, re-score, and check whether it (or its
  category) reappears in the top-k.
- `coverage_at_k` — fraction of the catalog that shows up in top-k lists
  across a sample of users (a cheap diversity check).

View runs with:

```bash
mlflow ui --backend-store-uri ./mlruns
```

## Running the tests

```bash
cd backend
source .venv/bin/activate  # if not already active
pytest
```

The suite runs against an in-memory SQLite DB with `get_db` /
`get_recommender` dependency overrides (see `tests/conftest.py`) — no seeded
`pharmaai.db` or trained `ml/artifacts/` required. It covers:

- `test_catalog.py`, `test_users.py`, `test_cart.py` — route-level behavior
  for browsing, the mock user session, and the cart/checkout flow.
- `test_recommend.py` — the `/recommend` route against stub recommenders,
  including `PredictionLog` writes.
- `test_recommender_scoring.py` — unit tests for `score_products` and
  `build_item_similarity` against a small hand-built `Artifacts` bundle
  (including the self-similarity diagonal fix).

## Repo structure

```
pharmaai/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entrypoint
│   │   ├── db.py               # SQLAlchemy engine/session
│   │   ├── models.py           # ORM models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── routes/              # catalog, cart, users, orders, recommend
│   │   └── services/recommender/
│   │       ├── base.py          # RecommenderService interface (the boundary)
│   │       ├── content_based.py # v1 implementation (loads ml/artifacts/)
│   │       ├── features.py      # item content-similarity (used by train.py)
│   │       └── artifacts.py     # artifact save/load + shared scoring logic
│   ├── ml/
│   │   ├── ingest_openfda.py    # real OTC product ingestion
│   │   ├── generate_synthetic.py # users + interactions w/ planted segments
│   │   ├── train.py             # trains recommender, logs to MLflow
│   │   ├── seed.py              # orchestrates ingest -> generate -> load DB
│   │   └── artifacts/           # trained model artifacts (gitignored)
│   └── tests/
│       ├── conftest.py          # in-memory DB + dependency-override fixtures
│       ├── test_catalog.py
│       ├── test_users.py
│       ├── test_cart.py
│       ├── test_recommend.py
│       └── test_recommender_scoring.py
├── frontend/                     # Vite + React + Tailwind
│   └── src/
│       ├── pages/                # Home, Catalog, ProductDetail, Login,
│       │                         # Cart, Checkout, OrderConfirmation, Account
│       ├── components/           # Header, Footer, ProductCard, StepIndicator, ...
│       └── lib/                  # api.ts, AuthContext, CartContext, categories
├── run.sh                        # one-command setup + run (see "Running it")
└── mlruns/                       # MLflow file store (gitignored)
```


## Roadmap / next versions

- **v1 (this build):** OTC store + content-based recommender + thin MLOps
  spine + prediction logging + test suite + one-command run.
- **Fork A — GenAI assistant:** swap `RecommenderService` for a
  RAG-grounded OTC guidance chatbot (hybrid retrieval over
  DailyMed/MedlinePlus, citations, groundedness guardrail, triage/escalation,
  eval harness).
- **Fork B — MLOps showcase:** swap in a drift-prone model (demand
  forecasting); the `PredictionLog` table already captures what real drift
  detection + retrain triggers + champion/challenger would need.
- **Fork C — store depth:** real search, payments, inventory
