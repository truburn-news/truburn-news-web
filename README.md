# Truburn Phase1 (FastAPI + HTMX)

Record-first prototype for Truburn Phase1. Focus: capture records with time resolution, request reviews (検証申請), and surface 5W1H/time ambiguity hints.

## Stack
- FastAPI, SQLAlchemy async, PostgreSQL (asyncpg)
- HTMX + Jinja templates (server-driven UI)
- Minimal AI scope: 5W1H/time ambiguity heuristic only (補助的)

## Quickstart (local, non-Docker)
1) Prepare PostgreSQL manually (RenderなどのマネージドDBやローカルPostgres)。`DATABASE_URL` を `.env` に設定。（ドライバは `postgresql+psycopg_async://user:pass@host:port/db`）
2) `cp .env.example .env` して接続文字列と `SESSION_SECRET` を更新。
3) Install deps: `pip install -r requirements.txt`
4) Run migrations: `alembic upgrade head`
5) Run API/UI: `uvicorn app.main:app --reload`
6) Open: `http://localhost:8000/feed/live`

## Features (解像度/確定度を明示)
- Mock wallet login (UUID生成) with initial VP balance. No token/DAO/voting/money.
- Record creation with Resolution slider: set center datetime + resolution (hours) → server computes `time_occurred_start/end` and `resolution_level` (1-5) + multiplier (x1.0〜x2.5) automatically.
- Feeds: `/feed/live`, `/feed/investigating`, `/feed/archive` (VERIFIED/FALSIFIED) + `/case/{id}` detail.
- Review Request creation (72h default, configurable via env). Requires VP, 200+ char reason, counter-evidence URL. Auto-finalizes: 反証あり→FALSIFIED / 反証なし→VERIFIED.
- Vault page shows mock wallet, VP ledger, owned records, review requests.
- Batch: `python -m app.jobs.finalize_reviews` to finalize expired reviews (also executed on feed/detail access).

## Renderデプロイのポイント
- RenderではDocker未使用を想定。RuntimeはPython、Start Commandは `uvicorn app.main:app --host 0.0.0.0 --port 10000` のように設定。
- 環境変数に `DATABASE_URL` と `REVIEW_REQUEST_DURATION_HOURS` を設定。PostgreSQLはRenderのManaged PostgreSQLを利用。
- `requirements.txt` がビルド時にインストールされるため追加作業不要。起動前に `alembic upgrade head` を実行。
- `SESSION_SECRET` を安全な値にすること。
