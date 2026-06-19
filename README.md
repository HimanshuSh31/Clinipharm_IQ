# 💊 Pharmacy Management System

A full-featured pharmacy management web application built with **Python** and **Streamlit**, backed by **SQLite**. Supports separate Admin and Customer portals with secure authentication, inventory management, and order tracking.

---

## ✨ Features

### 🔐 Authentication & Security
- PBKDF2-HMAC-SHA256 password hashing (260,000 iterations, random 16-byte salt per password)
- Admin credentials loaded from environment variables — never hardcoded
- Input validation for email and phone number on sign-up

### 🛡️ Admin Portal
- **Drug Inventory** — Add, view, update, and delete drugs; includes price and image support
- **Low-Stock Alerts** — Banner warns when any drug falls at or below 10 units
- **Inventory Search** — Filter drugs by name or ID; low-stock rows highlighted in red
- **Customer Management** — View, update, and delete customer accounts
- **Order Management** — View all orders with line totals and per-customer summaries; delete orders

### 🛒 Customer Portal
- Browse available medicines with prices, expiry dates, and stock levels
- Quantity sliders with real-time order total preview before placing
- Atomic order placement — stock is decremented in the same transaction; full rollback on failure
- Order history with per-order totals

### 🗄️ Database
- **Normalised schema** — `OrderItems` join table replaces comma-string order storage
- **Atomic transactions** — every multi-step write rolls back completely on failure
- **Foreign key enforcement** — `PRAGMA foreign_keys = ON` on every connection
- **Check constraints** — `D_Qty >= 0` prevents negative stock at the DB level
- **Auto-migration** — `_run_migrations()` safely adds new columns to existing databases on startup

---

## 🖥️ Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io/) |
| Database | SQLite 3 (via Python stdlib) |
| Data display | [Pandas](https://pandas.pydata.org/) |
| Image handling | [Pillow](https://python-pillow.org/) |
| Password hashing | `hashlib` PBKDF2-HMAC-SHA256 (Python stdlib) |
| Testing | [pytest](https://pytest.org/) |

---

## 📁 Project Structure

```
Pharmacy_Management_System/
│
├── main.py              # App entry point — routing & session state
├── database.py          # All SQLite CRUD operations & migrations
├── auth.py              # Password hashing, validation & authentication
├── admin_ui.py          # Admin dashboard UI
├── customer_ui.py       # Customer-facing UI
│
├── drug_data.db         # SQLite database (auto-created on first run)
├── drugdatabase.sql     # Schema reference (valid SQLite SQL)
│
├── images/              # Drug images (referenced by D_Image column)
│
├── tests/
│   ├── conftest.py      # pytest fixtures — isolated in-memory DB per test
│   ├── test_database.py # 37 database CRUD & transaction tests
│   └── test_auth.py     # 25 auth, hashing & validation tests
│
├── requirements.txt
├── pytest.ini
└── .env.example         # Template for admin credential env vars
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Pharmacy_Management_System.git
cd Pharmacy_Management_System
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure admin credentials *(optional but recommended)*

Copy `.env.example` to `.env` and set your credentials:

```bash
cp .env.example .env
```

```ini
PHARMACY_ADMIN_USER=your_admin_username
PHARMACY_ADMIN_PASS=your_secure_password
```

> If these are not set, the app falls back to `admin` / `admin` and logs a warning.

### 5. Run the app

```bash
streamlit run main.py
```

Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## 🧪 Running Tests

```bash
python -m pytest tests\ -v
```

The test suite runs **62 tests** against a fresh in-memory SQLite database — no running Streamlit server required.

```
62 passed in ~2.5s
```

### What's tested

| File | Tests | Coverage |
|---|---|---|
| `test_database.py` | 37 | All CRUD, atomic order placement, rollback on failure, CASCADE delete |
| `test_auth.py` | 25 | Password hashing uniqueness, verify correct/wrong/malformed, email & phone validators, customer auth |

---

## 🗄️ Database Schema

```sql
Customers  (C_Email PK, C_Name, C_Password, C_State, C_Number)
Drugs      (D_id PK, D_Name, D_ExpDate, D_Use, D_Qty >= 0, D_Price, D_Image)
Orders     (O_id PK, O_Name, O_Timestamp)
OrderItems (OI_id PK, O_id FK->Orders, D_id FK->Drugs,
            D_name, quantity > 0, unit_price)
```

- Deleting an `Orders` row cascades to its `OrderItems`
- The full schema with views is in [`drugdatabase.sql`](drugdatabase.sql)

---

## 📸 Drug Images

Place image files inside the `images/` folder. When adding a drug via the Admin portal, enter the filename (e.g. `aspirin.jpg`) in the **Image filename** field. The image will then be displayed on the customer's medicine catalogue.

---

## 🔒 Security Notes

| Concern | Approach |
|---|---|
| Password storage | PBKDF2-HMAC-SHA256, unique salt per password |
| Admin credentials | Environment variables (`PHARMACY_ADMIN_USER`, `PHARMACY_ADMIN_PASS`) |
| SQL injection | Parameterised queries throughout (`?` placeholders) |
| Negative stock | `CHECK(D_Qty >= 0)` DB constraint + app-level guard |

---

## 👤 Author

**Made by Himanshu Sharma**

---

## 📄 License

This project is for educational purposes.
