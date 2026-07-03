# Data Privacy

## Ephemeral Sessions

- **Authentication**: Session-based. User credentials (`alice`/`alice`, `bob`/`bob`)
  are stored in the SQLite database with werkzeug password hashing.
- **API keys**: Cloud LLM API keys are stored in the **Flask session cookie**
  (client-side, signed). They are never persisted to the database.
- **Chat history**: No chat history is stored server-side. LLM interactions are
  stateless unless the client sends history in the request body.

## Database

- **SQLite**: Two local files (`pizza_shop.db`, `catering_sql_lab.db`)
- **Default data**: Pre-populated with sample pizzas, comments, users, and
  routing flags on first startup
- **Data isolation**: The secondary `catering_sql_lab.db` is used exclusively
  by the catering SQL tool lab

## Docker Deployments

- Docker volumes persist the SQLite databases across restarts
- `docker compose down -v` removes all persistent data

## What Not to Store

Do not enter real credentials, real PII, or production API keys. The app's
vulnerabilities could expose any data stored in the database or session.
