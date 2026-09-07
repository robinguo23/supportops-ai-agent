# Container deployment

SupportOps can run as three containers:

- a PostgreSQL 16 database with pgvector;
- a FastAPI backend on port 8000;
- a React production build served by Nginx on port 5173.

## Run locally

Create a local environment file and add valid AI provider keys:

```bash
cp .env.example .env
docker compose up --build -d
```

Check the services:

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:5173/health
```

Open the application at `http://localhost:5173`.

Stop the containers without deleting database data:

```bash
docker compose down
```

To also remove the local PostgreSQL volume:

```bash
docker compose down --volumes
```

## Production behavior

The frontend image is a static Vite build served by Nginx. Set `VITE_API_BASE_URL` while building the image. An empty value uses same-origin API requests, which is suitable when an Application Load Balancer routes frontend and API paths under one hostname.

The backend reads its database URL, allowed CORS origins, and AI provider configuration from runtime environment variables. Secrets must be supplied by the deployment platform and must not be built into either image.
