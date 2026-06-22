"""
demo_data.py — Seeds the database with sample drugs and a demo customer.

Called automatically on first startup (when the Drugs table is empty).
This ensures the live demo has meaningful content out of the box.

Demo credentials:
  Admin:    admin / Demo@2024
  Customer: demo@pharma.com / Demo@2024
"""

import logging
from database import drug_add_data, customer_add_data, drug_view_all_data
from auth import hash_password

logger = logging.getLogger(__name__)

DEMO_DRUGS = [
    {
        "id": "#P001", "name": "Paracetamol 500mg",
        "expdate": "2027-06-30", "use": "Relieves mild to moderate pain and reduces fever. Take 1-2 tablets every 4-6 hours.",
        "qty": 150, "price": 12.50, "category": "Pain Relief",
        "supplier": "Sun Pharma", "prescription": 0, "image": None,
    },
    {
        "id": "#A001", "name": "Aspirin 75mg",
        "expdate": "2027-03-31", "use": "Low-dose antiplatelet therapy. Helps prevent blood clots and heart attacks.",
        "qty": 80, "price": 18.00, "category": "Cardiovascular",
        "supplier": "Bayer", "prescription": 0, "image": None,
    },
    {
        "id": "#AMX01", "name": "Amoxicillin 250mg",
        "expdate": "2026-12-31", "use": "Broad-spectrum antibiotic for bacterial infections including throat, ear, and chest.",
        "qty": 60, "price": 45.00, "category": "Antibiotic",
        "supplier": "Cipla", "prescription": 1, "image": None,
    },
    {
        "id": "#VC01", "name": "Vitamin C 500mg",
        "expdate": "2028-01-31", "use": "Supports immune function and antioxidant protection. Take once daily with water.",
        "qty": 200, "price": 8.00, "category": "Supplement",
        "supplier": "Himalaya", "prescription": 0, "image": None,
    },
    {
        "id": "#OMZ01", "name": "Omeprazole 20mg",
        "expdate": "2027-09-30", "use": "Proton pump inhibitor. Treats acid reflux, GERD, and stomach ulcers.",
        "qty": 7, "price": 32.00, "category": "Gastric",
        "supplier": "AstraZeneca", "prescription": 1, "image": None,
    },
    {
        "id": "#CTZ01", "name": "Cetirizine 10mg",
        "expdate": "2027-11-30", "use": "Antihistamine for allergic rhinitis, hay fever, hives, and itching.",
        "qty": 120, "price": 22.50, "category": "Antihistamine",
        "supplier": "UCB Pharma", "prescription": 0, "image": None,
    },
    {
        "id": "#MET01", "name": "Metformin 500mg",
        "expdate": "2027-04-30", "use": "First-line oral medication for Type 2 diabetes. Controls blood sugar levels.",
        "qty": 5, "price": 28.00, "category": "Antidiabetic",
        "supplier": "Merck", "prescription": 1, "image": None,
    },
    {
        "id": "#IB01", "name": "Ibuprofen 400mg",
        "expdate": "2027-08-31", "use": "NSAID anti-inflammatory. Relieves pain, fever, and swelling. Take with food.",
        "qty": 100, "price": 15.00, "category": "Pain Relief",
        "supplier": "Abbott", "prescription": 0, "image": None,
    },
    {
        "id": "#VD01", "name": "Vitamin D3 1000 IU",
        "expdate": "2028-06-30", "use": "Supports bone health, immune system, and calcium absorption. Take once daily.",
        "qty": 90, "price": 35.00, "category": "Supplement",
        "supplier": "Pfizer", "prescription": 0, "image": None,
    },
    {
        "id": "#AZI01", "name": "Azithromycin 500mg",
        "expdate": "2026-11-30", "use": "Macrolide antibiotic for respiratory tract, skin, and soft tissue infections.",
        "qty": 8, "price": 85.00, "category": "Antibiotic",
        "supplier": "Cipla", "prescription": 1, "image": None,
    },
]

DEMO_CUSTOMERS = [
    {
        "name": "Demo User",
        "email": "demo@pharma.com",
        "password": "Demo@2024",
        "state": "Maharashtra",
        "phone": "+91 9876543210",
    },
]


def seed_demo_data() -> None:
    """Seed demo drugs and customer if the Drugs table is empty."""
    if drug_view_all_data():
        return   # already has data — do not reseed

    logger.info("Seeding demo data...")

    drugs_added = 0
    for d in DEMO_DRUGS:
        ok = drug_add_data(
            d["name"], d["expdate"], d["use"], d["qty"], d["id"],
            d["price"], d["image"], d["category"], d["supplier"], d["prescription"]
        )
        if ok:
            drugs_added += 1

    for c in DEMO_CUSTOMERS:
        customer_add_data(
            c["name"], hash_password(c["password"]),
            c["email"], c["state"], c["phone"]
        )

    logger.info("Demo seed complete: %d drugs, %d customer(s).", drugs_added, len(DEMO_CUSTOMERS))
