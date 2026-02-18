# System Wycen AI+ML (B2B Pricing Engine)

[![CI/CD Pipeline](https://github.com/LukaszZinczuk/System-Wycen-AI-ML/actions/workflows/ci.yml/badge.svg)](https://github.com/LukaszZinczuk/System-Wycen-AI-ML/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Angular 16](https://img.shields.io/badge/angular-16-red.svg)](https://angular.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Enterprise-grade B2B pricing system with AI-powered scoring, built with FastAPI, Angular, and Machine Learning.

## 🎯 Project Overview

A complete pricing engine for B2B services that uses **hybrid AI scoring** (Machine Learning + Rule-Based) to automatically calculate prices, prioritize clients, and optimize revenue.

### Key Features

- **🤖 AI-Powered Pricing**: Hybrid scoring system combining Random Forest ML model (70%) with business rules (30%)
- **📊 Real-time Analytics**: Dashboard with KPIs, charts, and insights
- **🔐 Enterprise Security**: JWT auth, rate limiting, OWASP compliance
- **📈 Scalable Architecture**: Microservices-ready with async task processing
- **🧪 Fully Tested**: Unit, integration, and E2E tests with CI/CD pipeline

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Angular 16)                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐ │
│  │  Calculator │ │  Dashboard  │ │   Offers    │ │   Login    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API / JSON
┌────────────────────────────┴────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     API Layer (Routers)                   │   │
│  │  /auth  │  /companies  │  /offers  │  /admin  │  /health │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐   │
│  │  Services   │ │ Repositories│ │      Middleware         │   │
│  │ - Pricing   │ │ - Company   │ │ - Auth (JWT)            │   │
│  │ - ML        │ │ - Offer     │ │ - Rate Limiting         │   │
│  │             │ │ - User      │ │ - Security Headers      │   │
│  └─────────────┘ └─────────────┘ │ - Request Logging       │   │
│                                   └─────────────────────────┘   │
└─────────────┬────────────────────────────┬──────────────────────┘
              │                            │
┌─────────────▼────────────┐  ┌────────────▼─────────────────────┐
│   PostgreSQL Database    │  │        Redis + Celery            │
│   - Users, Companies     │  │   - Async Tasks                  │
│   - Offers, Industries   │  │   - Scheduled Jobs               │
│   - Alembic Migrations   │  │   - ML Retraining                │
└──────────────────────────┘  └──────────────────────────────────┘
```

---

## 🧱 Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.12** | Core language |
| **FastAPI** | REST API framework |
| **SQLAlchemy + Alembic** | ORM & migrations |
| **PostgreSQL** | Primary database |
| **Pydantic** | Data validation |
| **Scikit-Learn** | ML model (Random Forest) |
| **Celery + Redis** | Async task processing |
| **JWT (python-jose)** | Authentication |
| **pytest** | Testing framework |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Angular 16** | Frontend framework |
| **TypeScript** | Type-safe JavaScript |
| **RxJS** | Reactive programming |
| **Angular Material** | UI components |
| **Chart.js** | Data visualization |
| **Jasmine/Karma** | Unit testing |

### DevOps & Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker & Docker Compose** | Containerization |
| **GitHub Actions** | CI/CD pipeline |
| **NGINX** | Frontend serving & reverse proxy |
| **AWS (optional)** | Cloud deployment (ECR, ECS, Fargate) |

---

## 🚀 Quick Start

### Prerequisites
- **Docker** & **Docker Compose** (v2+)
- **Git**

### 1. Clone & Run
```bash
git clone https://github.com/LukaszZinczuk/System-Wycen-AI-ML.git
cd System-Wycen-AI-ML
docker-compose up --build
```

### 2. Access the Application
| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:4200 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/health |
| **Metrics** | http://localhost:8000/metrics |

### 3. Default Credentials
```
Email: admin@example.com
Password: admin123
```

---

## 🧠 AI Scoring System

### Hybrid Scoring Algorithm

The system uses a **weighted hybrid approach**:

```
Final Score = (0.7 × ML Score) + (0.3 × Rule Score)
```

#### ML Score (70%) - Random Forest Regressor
**Input Features:**
- `employees_count` - Company size
- `region` - Geographic location
- `premium` - Premium service flag
- `avg_order_value` - Historical average order value
- `offers_count` - Number of previous offers
- `industry_risk_factor` - Industry-specific risk

**Output:** Profitability score (0-100)

#### Rule Score (30%) - Business Rules
| Condition | Points |
|-----------|--------|
| Employees ≥ 100 | +15 |
| Premium Service | +10 |
| Region = Mazowieckie | +5 |
| Avg Order Value > 20k | +10 |
| Previous Offers ≥ 3 | +5 |

### Priority Levels & Actions
| Score Range | Priority | Action |
|-------------|----------|--------|
| 0-40 | **LOW** | Standard processing |
| 41-70 | **STANDARD** | Regular attention |
| 71-100 | **VIP** | 5% discount + priority handling |

---

## 🔐 Security Features

### OWASP Compliance
- ✅ **Rate Limiting**: 100 req/min, 2000 req/hour per IP
- ✅ **Security Headers**: CSP, HSTS, X-Frame-Options, etc.
- ✅ **Input Sanitization**: XSS & injection prevention
- ✅ **JWT Authentication**: Secure token-based auth
- ✅ **Password Hashing**: bcrypt with salt

### Security Headers
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## 📁 Project Structure

```
.
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI pipeline (tests, lint, build)
│       └── deploy.yml          # Deployment pipeline (AWS)
├── backend/
│   ├── alembic/                # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── app/
│   │   ├── core/               # Config, security, logging
│   │   ├── middleware/         # Security, logging middleware
│   │   ├── models/             # SQLAlchemy models
│   │   ├── repositories/       # Data access layer
│   │   ├── routers/            # API endpoints
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic (pricing, ML)
│   │   ├── tasks/              # Celery async tasks
│   │   ├── celery_app.py       # Celery configuration
│   │   └── main.py             # FastAPI app entry
│   ├── tests/
│   │   ├── unit/               # Unit tests
│   │   └── integration/        # API integration tests
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── calculator/     # Pricing calculator
│   │   │   ├── dashboard/      # Admin dashboard
│   │   │   ├── offers/         # Offers list
│   │   │   └── services/       # API & Auth services
│   │   └── environments/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/unit -v

# Run only integration tests
pytest tests/integration -v
```

### Frontend Tests
```bash
cd frontend

# Run tests
npm run test

# Run tests with coverage (CI mode)
npm run test:ci

# Run linting
npm run lint
```

### Test Coverage Goals
- Backend: >80% coverage
- Frontend: >70% coverage

---

## 📊 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/token` | Login (OAuth2 password flow) |
| POST | `/api/auth/register` | Register new user |

### Companies
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/companies/` | List all companies |
| POST | `/api/companies/` | Create new company |
| GET | `/api/companies/{id}` | Get company by ID |

### Offers
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/offers/` | List offers |
| POST | `/api/offers/` | Create & calculate offer |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Dashboard statistics |
| POST | `/api/admin/recalc_scores` | Recalculate all scores |

### Health & Monitoring
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/ready` | Readiness probe |
| GET | `/health/live` | Liveness probe |
| GET | `/health/detailed` | Detailed system status |
| GET | `/metrics` | Prometheus metrics |

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
Trigger: Push to main/develop, Pull Requests

Jobs:
├── backend-test       # pytest + coverage
├── backend-lint       # flake8, black, isort, mypy
├── frontend-test      # ng test + coverage
├── security-scan      # bandit, safety
├── docker-build       # Build images
└── integration-test   # Docker Compose smoke tests
```

### Deployment (AWS)
- **ECR**: Container registry
- **ECS Fargate**: Serverless containers
- **RDS**: Managed PostgreSQL
- **ElastiCache**: Managed Redis

---

## 📈 Monitoring & Observability

### Logging
- Structured JSON logging (production)
- Colored console output (development)
- Correlation IDs for request tracing
- Request/response timing

### Metrics (Prometheus-compatible)
- `http_requests_total` - Total request count
- `http_errors_total` - Error count
- `http_request_duration_seconds` - Latency
- `process_memory_bytes` - Memory usage
- `process_cpu_percent` - CPU usage

### Health Checks
- **Liveness**: Application is running
- **Readiness**: All dependencies available
- **Detailed**: Full system diagnostics

---

## 🛠️ Development

### Local Development (without Docker)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database migrations
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
ng serve
```

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...` | Database connection |
| `SECRET_KEY` | - | JWT signing key |
| `CELERY_BROKER_URL` | `redis://...` | Celery broker |
| `LOG_LEVEL` | `INFO` | Logging level |
| `JSON_LOGS` | `false` | JSON log format |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Quality Standards
- All tests must pass
- Code must be formatted with `black`
- Imports sorted with `isort`
- Type hints required (Python)
- TypeScript strict mode (Angular)

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Łukasz Zinczuk** - [GitHub](https://github.com/LukaszZinczuk)

Created for portfolio demonstration purposes.

**Technologies demonstrated:**
- Full-stack development (Python + TypeScript)
- Machine Learning integration
- RESTful API design
- Modern frontend (Angular + RxJS)
- DevOps practices (Docker, CI/CD)
- Security best practices (OWASP)
- Clean architecture patterns
