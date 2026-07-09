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

For Supabase Storage-backed dashboard assets, set these backend-only values in `backend/.env`:

```powershell
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_SERVICE_ROLE_KEY=[service-role-key]
SUPABASE_STORAGE_BUCKET=mi-demo-assets
```

When those values are present, FastAPI uploads the bundled topographic map to Supabase Storage through `SupabaseService.ensure_topographic_map_asset()` and returns the public Storage URL to the frontend. Without them, local development falls back to the bundled static map.

No authentication is implemented for this PoC. The frontend does not use Supabase keys; it talks to the FastAPI backend only.

## Demo Data Flow

1. Open the frontend and use the `Data Setup` tab.
2. Upload a JSON dataset.
3. FastAPI converts the JSON into SQLModel records.
4. The backend persists those records to the configured database. With a Supabase Postgres DSN, this writes to Supabase.
5. The dashboard and 3D region views load from persisted database records through FastAPI service methods.

Supabase Storage is used for the dashboard topographic map when Storage env vars are configured. The 3D region scene assets are still procedural Threlte/Three.js geometry generated from database records.

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
- `.github/workflows/deploy-staging.yml`: builds SHA-tagged backend/frontend images on `main`, publishes them to GHCR, runs Alembic, and deploys staging.
- `.github/workflows/deploy-production.yml`: builds release-tagged backend/frontend images on published `v#.#.#` releases, supports manual rollback by image tag, runs Alembic, and deploys prod.

Create the runtime secret from `kube/overlays/<env>/secret.template.yaml` with:

- `DATABASE_URL`: Supabase/Postgres connection string.
- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_SERVICE_ROLE_KEY`: backend-only service role key for Storage upload.
- `SUPABASE_STORAGE_BUCKET`: Storage bucket for dashboard assets, for example `mi-demo-assets`.

The expected deployed hosts are:

- Staging: `https://staging.mi.jackdra.com`
- Prod: `https://mi.jackdra.com`

GitHub deployment environments should provide:

- `APP_URL` environment variable, optional when using the default hosts above.
- `KUBE_CONFIG` secret with the target cluster kubeconfig.
- `GHCR_USERNAME` and `GHCR_TOKEN` secrets for the cluster image pull secret.
- `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and optionally `SUPABASE_STORAGE_BUCKET` secrets.

Render manifests before applying:

```powershell
kubectl kustomize kube/overlays/staging
kubectl kustomize kube/overlays/prod
```
