| Component | Purpose | Docs |
|------------|----------|------|
| **FastAPI** | Backend web framework to build REST APIs | [FastAPI Docs](https://fastapi.tiangolo.com/) |
| **SQLModel / SQLAlchemy** | ORM (object–relational mapper) for database models | [SQLModel Docs](https://sqlmodel.tiangolo.com/) |
| **Alembic** | Database migrations (keeps DB schema in sync) | [Alembic Docs](https://alembic.sqlalchemy.org/) |
| **PostgreSQL** | Relational database running in Docker | [Postgres Docs](https://www.postgresql.org/docs/) |
| **Plaid API** | Securely links user bank accounts and retrieves transactions | [Plaid API Docs](https://plaid.com/docs/api/) |
| **Uvicorn** | High-performance web server for FastAPI | [Uvicorn Docs](https://www.uvicorn.org/) |
| **Docker** | Container system used to run Postgres locally | [Docker Docs](https://docs.docker.com/get-started/) |


---

## INSTALLATION GUIDE

---

## ⚙️ 1. Clone and Open in VS Code

```bash
git clone https://github.com/yourusername/lucentia.git
cd lucentia/backend
code .
````

---

##  2. Set Up a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

* **Windows (PowerShell)**

  ```bash
  .venv\Scripts\activate
  ```
* **Mac/Linux**

  ```bash
  source .venv/bin/activate
  ```

Check that it’s active — your terminal prompt should begin with `(.venv)`.

---

##  3. Install All Dependencies

Run **this single pip install command** to get everything the backend needs:

```bash
pip install fastapi uvicorn sqlmodel sqlalchemy psycopg2-binary alembic python-dotenv requests plaid-python black isort pylint
```

### What Each Package Does

| Package                      | Purpose                                     |
| ---------------------------- | ------------------------------------------- |
| `fastapi`                    | Core web API framework                      |
| `uvicorn`                    | Web server for FastAPI                      |
| `sqlmodel`                   | Defines and interacts with database models  |
| `sqlalchemy`                 | Backend ORM engine used by SQLModel         |
| `psycopg2-binary`            | PostgreSQL driver                           |
| `alembic`                    | Database schema migrations                  |
| `python-dotenv`              | Loads environment variables from `.env`     |
| `requests`                   | HTTP client for external API calls          |
| `plaid-python`               | Official Plaid API SDK                      |
| `black` / `isort` / `pylint` | Formatting and linting tools for clean code |

>  **Note:** If VS Code shows `Import "fastapi" could not be resolved`, fix it by:
>
> * Opening **Command Palette (Ctrl+Shift+P)**
> * Typing “Python: Select Interpreter” → choose `.venv`

---

##  4. Run PostgreSQL with Docker

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Start your local Postgres container:

```bash
docker run --name lucentia_db \
  -e POSTGRES_PASSWORD=lucentia \
  -e POSTGRES_USER=lucentia \
  -e POSTGRES_DB=lucentia \
  -p 5432:5432 \
  -d postgres
```

Confirm it’s running:

```bash
docker ps
```

To stop or restart:

```bash
docker stop lucentia_db
docker start lucentia_db
```

---

##  5. Configure Environment Variables

Create a `.env` file in `/backend` and paste the following:

```env
PLAID_CLIENT_ID=your_client_id_here
PLAID_SECRET=your_secret_here
PLAID_ENV=sandbox
PLAID_PRODUCTS=transactions
PLAID_COUNTRY_CODES=US
PLAID_OAUTH_REDIRECT_URI=http://localhost:8000/oauth-callback
DATABASE_URL=postgresql+psycopg2://lucentia:lucentia@localhost:5432/lucentia
```

> Later, once approved for real banks:
>
> * Change `PLAID_ENV=sandbox` → `development`
> * Replace with your **Development** Plaid credentials.

---

##  6. Initialize the Database Schema

Create the database tables:

```bash
alembic upgrade head
```

Or if you have a helper file:

```bash
python -m app.create_db
```

---

##  7. Run the Backend Server

```bash
uvicorn app.main:app --reload
```

Then visit:
 [http://localhost:8000/docs](http://localhost:8000/docs)

This opens FastAPI’s Swagger UI where you can:

* Connect your bank (Plaid sandbox)
* Refresh insights
* View generated spending data

---

##  8. Frontend Setup

If you’re also running the **React frontend**:

```bash
cd frontend
npm install
npm start
```

Ensure backend is running at:

```
http://localhost:8000/
```

Frontend will connect automatically to FastAPI for Plaid routes and insights.

---
