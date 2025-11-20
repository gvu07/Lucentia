

# **Lucentia**

*A personal finance insights platform that transforms raw bank data into clear, actionable recommendations.*

Lucentia connects securely to financial accounts via Plaid, ingests real-world transaction data, and turns it into intuitive insights instead of overwhelming tables. The project demonstrates a full end-to-end product: secure data ingestion, a modular insights engine, and a polished, modern frontend.

---

## **Founders**

* **Suyash Ojha**
* **Giang Anh Vu**
* **Elijah Ford**

---

## **🌟 Highlights**

* **Secure Account Linking:** Plaid Link flow to connect accounts, sync balances, and fetch transaction history.
* **Rich Financial Dashboard:** Balances, cash-flow trends, category breakdowns, merchant analytics, and full transaction views.
* **Insight Engine:**

  * Spending patterns & habits
  * Subscriptions detection
  * Cash buffer analysis
  * Merchant loyalty & frequency trends
  * Sustainability & local-impact estimations
  * Income stability & cash-flow modeling
  * Goal-oriented long-term financial recommendations
* **Modern Auth:** JWT-protected API routes with auto-refresh and role-aware UX.
* **Frontend Polish:** Interactive UI built with React, Tailwind, and Recharts for dynamic data visualization.
* **API Documentation:** Auto-generated FastAPI docs available at `/docs`.

---

## **🧱 Stack at a Glance**

### **Backend**

* FastAPI
* SQLAlchemy ORM
* PostgreSQL
* Alembic migrations
* Plaid Python SDK
* JWT auth via `python-jose`
* Pydantic validation
* Optional Redis caching
* Pytest suite for insights engine

### **Frontend**

* React 18 + Vite
* Tailwind CSS
* React Router
* Axios
* `react-plaid-link`
* Recharts

### **Tooling**

* Poetry (Python dependency management)
* ESLint (JS/JSX linting)
* Docker Compose (Postgres, Redis, Backend)

---

## **📁 Project Structure**

```
lucentia/
├── backend/
│   └── app/
│       ├── main.py               # FastAPI entrypoint
│       ├── api/                  # Routers & endpoints
│       ├── auth/                 # JWT handling
│       ├── models/               # SQLAlchemy models
│       ├── schemas/              # Pydantic schemas
│       ├── crud/                 # Data-layer operations
│       ├── insights/             # Insight engine + registry
│       ├── clients/              # Plaid client wrapper
│       └── core/                 # Settings, config, deps
│
├── backend/scripts/
│   ├── seed_dli_users.py         # Deterministic demo user seeding
│   └── sample_fixtures/          # Testing sample data
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api/                  # Axios client
│       ├── components/           # Reusable UI components
│       ├── pages/                # Dashboard, accounts, auth, insights
│       └── hooks/                # Data + UI logic
│
├── docker-compose.yml            # Postgres, Redis, Backend
└── README.md
```

---

## **🚀 Run Locally**

### **Prerequisites**

* Python **3.9+**
* Node **16+**
* Postgres **12+** (or Docker installed)

---

### **Backend Setup**

```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

### **Frontend Setup**

```bash
cd frontend
npm install
npm run dev
```

### **With Docker Compose**

```bash
docker-compose up --build
```

This starts:

* Postgres
* Redis
* FastAPI backend

Then separately run:

```bash
cd frontend
npm run dev
```

---

## **📬 Contact**

Suyash: suyasho@umich.edu
Giang: gvu@umich.edu
Elijah: felijah@umich.edu

If you're evaluating Lucentia or want to discuss the architecture, feel free to reach out to any of the founders. The project is actively evolving with a long-term vision of becoming a full personal finance OS.

---
