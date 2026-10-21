# SkyBook - Flight Booking System

A full-featured Flight Booking web application built with **Flask**, **MongoDB Atlas**, and pure **HTML / CSS / JavaScript** (Jinja2 templates, no React).

---

## Quick Start

### 1. Run the Application
The main python entry point is [`app.py`](file:///c:/Users/sakth/.gemini/antigravity/scratch/flight_booking/app.py):

```bash
python app.py
```

The application will start on **http://127.0.0.1:5000**.

*(Note: `python run.py` also works as a backwards-compatible alias.)*

---

## Default Accounts

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@flights.com` | `admin123` |
| **Demo User** | `testuser_e2e@example.com` | `password123` |

---

## Features

- **MongoDB Document Schema**:
  - Embedded documents for route, schedule, aircraft specs, pricing, and seat info.
  - Embedded arrays for flight photo galleries and cabin amenities.
  - Historical snapshot of flight details preserved inside each booking record.
  - Atomic inventory decrement and increment via MongoDB `$inc`.
- **Flight Search & Filtering**: Multi-parameter search querying embedded document fields via dot notation.
- **Flight Details**: Aircraft info, photo gallery, seat availability, and fare breakdown.
- **Booking Flow**: Dynamic multi-passenger forms, instant seat calculation, and digital boarding pass generation.
- **Tiered Cancellation Policy**:
  - Cancelled within 3 hours: **100% full refund**.
  - Cancelled after 3 hours: **50% half refund**.
  - Automatic seat inventory restoration upon cancellation.
- **Admin Hub** (`/admin`): Live statistics, flight catalog management, flight photo management, and booking oversight.

---

## Testing

- **Comprehensive E2E Verification**:
  ```bash
  python test_e2e.py
  ```
- **Cancellation Policy Unit Tests**:
  ```bash
  python test_cancellation.py
  ```
