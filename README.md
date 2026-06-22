# 💊 Pharmacy Management System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pharmacymanagementsystem-himanshush31.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-lightblue?logo=sqlite&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-73%20passed-brightgreen?logo=pytest&logoColor=white)
![CI](https://github.com/HimanshuSh31/Pharmacy_Management_System/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/License-Educational-orange)

A full-featured pharmacy management web application built with **Python** and **Streamlit**, backed by **SQLite**. Supports separate Admin and Customer portals with secure authentication, inventory management, and order tracking.

---

## 🚀 Live Demo

**[▶ Open Live Demo](https://pharmacymanagementsystem-himanshush31.streamlit.app)**

| Role | Username / Email | Password |
|---|---|---|
| 🛡️ Admin | `admin` | `Demo@2024` |
| 🛒 Customer | `demo@pharma.com` | `Demo@2024` |

> The demo database resets when the app is redeployed. All data you enter is for demonstration only.

---

## ✨ Features

### 🔐 Authentication & Security
- PBKDF2-HMAC-SHA256 password hashing (260,000 iterations, unique 16-byte salt per password)
- Admin credentials via environment variables / Streamlit secrets — never hardcoded
- Login rate limiting: locked for 5 minutes after 5 failed attempts
- Session timeout: auto-logout after 60 minutes of inactivity
- Password strength enforcement on sign-up

### 🛡️ Admin Portal
- **5 live metric cards** — Total Drugs, Low Stock, Customers, Orders, Revenue
- **Drug Inventory** — Add, view, update, delete with category, supplier, prescription flag
- **Image upload** — Upload drug photos directly from the browser
- **Bulk CSV Import** — Import hundreds of drugs at once with template download
- **Paginated drug list** — 20 drugs per page with search + category filter
- **Low-stock alerts** — Red banner + optional email notification (SMTP)
- **Expiry highlighting** — Red = expired · Orange = ≤30 days · Yellow = low stock
- **Customer Management** — View, search, update, delete accounts
- **Order Management** — Full order history with revenue by customer; CSV export
- **Cache layer** — `@st.cache_data` (30–120s TTL) with write-through invalidation

### 🛒 Customer Portal
- Browse medicines in a **3-column card grid** with category + prescription badges
- **Medicine search** and **category filter** dropdown
- Expired drugs shown as blocked cards (cannot be ordered)
- Expiring-soon warning badge (≤30 days)
- Quantity sliders with real-time per-item subtotal
- **Order confirmation step** — review full summary + total before placing
- Order history with per-order totals and CSV download
- **Customer profile sidebar** — view and update phone number

### 🗄️ Database
- **Normalised schema** — `OrderItems` join table
- **Atomic transactions** — full rollback on any failure
- **Foreign key enforcement** — `PRAGMA foreign_keys = ON`
- **Check constraints** — `D_Qty >= 0` prevents negative stock
- **Auto-migration** — `_run_migrations()` safely adds new columns on startup
- **New columns** — `D_Category`, `D_Supplier`, `D_Prescription`

---

## 🖥️ Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io/) |
| Database | SQLite 3 (Python stdlib) |
| Data display | [Pandas](https://pandas.pydata.org/) |
| Image handling | [Pillow](https://python-pillow.org/) |
| Password hashing | `hashlib` PBKDF2-HMAC-SHA256 (Python stdlib) |
| Email alerts | `smtplib` (Python stdlib) |
| Caching | `@st.cache_data` (Streamlit) |
| Testing | [pytest](https://pytest.org/) |
| CI | GitHub Actions |
| Deploy | Streamlit Community Cloud / Docker |

---

## 📁 Project Structure

```
Pharmacy_Management_System/
│
├── main.py              # Entry point — routing, session, auth screens
├── database.py          # All SQLite CRUD, schema migrations, bulk import
├── auth.py              # PBKDF2 hashing, validators, rate limiting helpers
├── admin_ui.py          # Admin dashboard UI (metrics, CRUD, import, alerts)
├── customer_ui.py       # Customer-facing UI (card grid, order flow)
├── data.py              # @st.cache_data read layer with invalidators
├── notifier.py          # SMTP low-stock email alerts
├── demo_data.py         # Seeds 10 demo drugs + 1 demo customer on first run
├── styles.py            # Master CSS + HTML component helpers
│
├── drug_data.db         # SQLite database (auto-created on first run)
├── drugdatabase.sql     # Schema reference with SQL views
│
├── images/              # Drug images (uploaded via admin UI)
│
├── tests/
│   ├── conftest.py      # pytest fixtures — isolated in-memory DB
│   ├── test_database.py # 40 CRUD & transaction tests
│   └── test_auth.py     # 33 auth, hashing & validation tests
│
├── .streamlit/
│   ├── config.toml           # Premium color theme
│   └── secrets.toml.example  # Secrets template for Streamlit Cloud
│
├── .github/workflows/ci.yml  # GitHub Actions: pytest on every push/PR
├── Dockerfile                # Production Docker image
├── docker-compose.yml        # One-command deploy
├── requirements.txt
├── pytest.ini
└── .env.example         # Environment variable template
```

---

## 🚀 Getting Started

### Option 1 — Streamlit Community Cloud (Recommended)

1. Fork this repository
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub
3. Click **New app** → select your fork → set main file to `main.py`
4. Under **Advanced settings → Secrets**, paste:
   ```toml
   PHARMACY_ADMIN_USER = "admin"
   PHARMACY_ADMIN_PASS = "YourSecurePassword"
   ```
5. Click **Deploy** — live in ~60 seconds ✅

### Option 2 — Docker (One command)

```bash
git clone https://github.com/HimanshuSh31/Pharmacy_Management_System.git
cd Pharmacy_Management_System
cp .env.example .env          # edit credentials
docker compose up --build
```
Open **[http://localhost:8501](http://localhost:8501)**

### Option 3 — Local Python

```bash
git clone https://github.com/HimanshuSh31/Pharmacy_Management_System.git
cd Pharmacy_Management_System
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # edit credentials
streamlit run main.py
```

---

## 🧑‍💼 Default Demo Credentials

| Role | Username / Email | Password |
|---|---|---|
| 🛡️ Admin | `admin` | `Demo@2024` |
| 🛒 Customer | `demo@pharma.com` | `Demo@2024` |

> Change admin credentials via the `.env` file or Streamlit Cloud secrets.

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

**73 tests · ~2.5s · in-memory SQLite · no Streamlit server required**

| File | Tests | Coverage |
|---|---|---|
| `test_database.py` | 40 | CRUD, atomic orders, rollback, CASCADE, low-stock, bulk import |
| `test_auth.py` | 33 | Password hashing, strength, email/phone validators, rate limiting |

---

## 🗄️ Database Schema

```sql
Customers  (C_Email PK, C_Name, C_Password, C_State, C_Number)
Drugs      (D_id PK, D_Name, D_ExpDate, D_Use, D_Qty >= 0,
            D_Price, D_Image, D_Category, D_Supplier, D_Prescription)
Orders     (O_id PK, O_Name, O_Timestamp, C_Email FK→Customers)
OrderItems (OI_id PK, O_id FK→Orders CASCADE,
            D_id FK→Drugs, D_name, quantity > 0, unit_price)
```

---

## 🔒 Security Notes

| Concern | Approach |
|---|---|
| Password storage | PBKDF2-HMAC-SHA256, unique random salt per password |
| Admin credentials | Environment variables / Streamlit Cloud secrets |
| SQL injection | Parameterised queries (`?` placeholders) throughout |
| Negative stock | `CHECK(D_Qty >= 0)` + app-level guard in `order_place()` |
| Brute force | 5-attempt lockout with 5-minute cooldown |
| Session hijack | 60-minute idle timeout |

---

## 📧 Low-Stock Email Alerts

Set these in `.env` or Streamlit Cloud secrets to enable the **📧 Email Alert** button:

```ini
SMTP_HOST   = smtp.gmail.com
SMTP_PORT   = 587
SMTP_USER   = you@gmail.com
SMTP_PASS   = your-16-char-app-password   # Gmail App Password
ALERT_EMAIL = admin@yourpharmacy.com
```

---

## 👤 Author

**Made by Himanshu Sharma**

---

## 📄 License

This project is for educational purposes.
