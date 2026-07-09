# MI Demo

Proof-of-concept control panel for a visual Murrumbidgee Irrigation operations dashboard.

The app is split into:

- `backend/`: FastAPI, SQLModel, Alembic, fake data ingestion, and notification generation.
- `frontend/`: SvelteKit, Threlte, Three.js, dashboard UI, and 3D region viewer.
- `planning/`: concept and implementation planning.

## Local Development

Backend:

```powershell
cd backend
uv sync --group dev
uv run alembic upgrade head
uv run backend
```

Frontend:

```powershell
cd frontend
bun install
bun run dev
```

By default the backend can run against local SQLite for development. For Supabase Postgres, set `DATABASE_URL` or `SUPABASE_DB_URL` in `backend/.env`.

No authentication is implemented for this PoC. The frontend does not use Supabase keys; it talks to the FastAPI backend only.

## Demo Data Flow

The bundled JSON file at `demo_data/default_dataset.json` is a setup template, not the runtime source of truth.

1. Open the frontend and use the `Data Setup` tab.
2. Upload a JSON dataset, or import the bundled template.
3. FastAPI converts the JSON into SQLModel records.
4. The backend persists those records to the configured database. With a Supabase Postgres DSN, this writes to Supabase.
5. The dashboard and 3D region views load from persisted database records through FastAPI service methods.

Supabase Storage is not used yet. The current 3D scene assets are procedural Threlte/Three.js geometry generated from database records.

## Local Containers

```powershell
docker compose up --build
```

This starts:

- Frontend: `http://127.0.0.1:3300`
- Backend: `http://127.0.0.1:8300`
- Postgres: `127.0.0.1:57432`

## Deployment

Deployment follows the sibling project pattern:

- `frontend/Dockerfile`: SvelteKit adapter-node runtime on port `3000`.
- `backend/Dockerfile`: FastAPI/uv runtime on port `8000`.
- `kube/base`: backend, frontend, and ingress resources.
- `kube/overlays/staging`: `mi-demo-staging`, `ghcr.io/jackdra/mi-demo-*:{staging}`.
- `kube/overlays/prod`: `mi-demo-prod`, `ghcr.io/jackdra/mi-demo-*:{prod}`.

Create the runtime secret from `kube/overlays/<env>/secret.template.yaml` with:

- `DATABASE_URL`: Supabase/Postgres connection string.

The expected deployed hosts are:

- Staging: `https://staging.mi-demo.jackdra.com`
- Prod: `https://mi-demo.jackdra.com`

Render manifests before applying:

```powershell
kubectl kustomize kube/overlays/staging
kubectl kustomize kube/overlays/prod
```
