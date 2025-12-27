# Truburn Phase1 (FastAPI + HTMX)

Record-first prototype for Truburn Phase1. Focus: capture records with time resolution, request reviews (検証申請), and surface 5W1H/time ambiguity hints.

## Stack
- FastAPI, SQLAlchemy async, PostgreSQL (asyncpg)
- HTMX + Jinja templates (server-driven UI)
- Minimal AI scope: 5W1H/time ambiguity heuristic only (補助的)

## Quickstart (local, non-Docker)
1) Prepare PostgreSQL manually (RenderなどのマネージドDBやローカルPostgres)。`DATABASE_URL` を `.env` に設定。（ドライバは `postgresql+psycopg_async://user:pass@host:port/db`）
2) `cp .env.example .env` して接続文字列を更新。
3) Install deps: `pip install -r requirements.txt`
4) Run API/UI: `uvicorn app.main:app --reload`
5) Open: `http://localhost:8000/records`

Tables auto-create on startup (prototype). Prefer migrations later.

## Features (解像度/確定度を明示)
- Record creation with Resolution Slider: set center datetime + resolution (hours) → server computes `time_occurred_start/end`.
- Review Request creation (Review期間=環境変数の時間、例72h)。内部VPストアのみ。
- Record detail shows 5W1H/time ambiguity hints (確定ではない、補助のみ)。
- No tokens/DAO/voting; Review Request only.

## Renderデプロイのポイント
- RenderではDocker未使用を想定。RuntimeはPython、Start Commandは `uvicorn app.main:app --host 0.0.0.0 --port 10000` のように設定。
- 環境変数に `DATABASE_URL` と `REVIEW_REQUEST_DURATION_HOURS` を設定。PostgreSQLはRenderのManaged PostgreSQLを利用。
- `requirements.txt` がビルド時にインストールされるため追加作業不要。マイグレーションが必要になったら別途コマンドを準備。

## Next steps
- Add migrations (Alembic) and proper validation.
- Harden time parsing/timezone handling.
- Extend Review workflow (status transitions, audit log).
