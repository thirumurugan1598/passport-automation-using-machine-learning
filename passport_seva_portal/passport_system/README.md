# 🇮🇳 Passport Seva Portal — India

**A production-grade Passport Automation System** built with Flask, SQLite, and a custom ML verification engine. Simulates the real Government of India passport processing pipeline end-to-end.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies (only Flask + Werkzeug needed)
pip install flask werkzeug

# 2. Run the application
python run.py

# 3. Open in browser
# → http://localhost:5000
```

---

## 🔐 Demo Credentials

| Role | Email | Password | Access |
|------|-------|----------|--------|
| 🛡️ Admin Officer | `admin@passport.gov.in` | `Admin@123` | Full dashboard, issue passports |
| 👮 Police Officer | `police@passport.gov.in` | `Police@123` | Background verification queue |
| 👤 Citizen | Register at `/auth/register` | Your choice | Apply, track applications |

---

## 🔄 Full Workflow

```
CITIZEN               ML ENGINE              POLICE               ADMIN
   │                      │                     │                    │
   │── Register ─────────►│                     │                    │
   │── Login ────────────►│                     │                    │
   │── Fill Form ────────►│                     │                    │
   │── Upload Docs ──────►│                     │                    │
   │                      │◄── Auto-triggered   │                    │
   │                      │   Face Match        │                    │
   │                      │   Aadhaar Verify    │                    │
   │                      │   Doc Validity      │                    │
   │◄── ML Result ────────│   Address Check     │                    │
   │                      │                     │                    │
   │              [IF PASSED → status: ml_verified]                  │
   │                      │──────────────────►  │                    │
   │                      │                     │── Review ML Data   │
   │                      │                     │── Background Check │
   │                      │                     │── Approve/Reject   │
   │                      │                     │                    │
   │              [IF APPROVED → status: police_approved]            │
   │                      │                     │──────────────────► │
   │                      │                     │                    │── Final Review
   │                      │                     │                    │── Issue Passport
   │◄── Status Updates ───────────────────────────────────────────── │
   │── Track Anytime ────►│ (public tracking page)                   │
```

---

## 📁 Project Structure

```
passport_system/
├── run.py                      ← Entry point (use this to start)
├── app.py                      ← Flask app factory
├── passport.db                 ← SQLite database (auto-created)
├── uploads/                    ← Document uploads (auto-created)
│
├── app/
│   ├── __init__.py
│   ├── database.py             ← DB init, schema, connection helpers
│   ├── ml_model.py             ← ML verification engine (extensible)
│   ├── utils.py                ← Auth decorators, validators, generators
│   │
│   ├── routes/
│   │   ├── main.py             ← Home page, status tracking
│   │   ├── auth.py             ← Register, Login, Logout
│   │   ├── citizen.py          ← Dashboard, Apply, View application
│   │   ├── police.py           ← Police dashboard, review, verify
│   │   └── admin.py            ← Admin dashboard, approve, issue
│   │
│   ├── templates/
│   │   ├── base.html           ← Shared layout, nav, footer
│   │   ├── main/
│   │   │   ├── index.html      ← Landing page with passport card visual
│   │   │   └── track.html      ← Public status tracking
│   │   ├── auth/
│   │   │   ├── login.html      ← Login with demo credentials panel
│   │   │   └── register.html   ← Citizen registration
│   │   ├── citizen/
│   │   │   ├── dashboard.html  ← Application cards with progress bars
│   │   │   ├── apply.html      ← Multi-step application form + uploads
│   │   │   └── view_application.html ← Full detail + ML score bars
│   │   ├── police/
│   │   │   ├── dashboard.html  ← Verification queue table
│   │   │   └── review.html     ← Full review + decision panel
│   │   └── admin/
│   │       ├── dashboard.html  ← Analytics + filterable table
│   │       ├── review.html     ← Final approval + passport issuance
│   │       └── users.html      ← User management
│   │
│   └── static/
│       ├── css/main.css        ← Full Indian gov portal design (~1000 lines)
│       └── js/main.js          ← Animations, form helpers
```

---

## 🗄️ Database Schema

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| full_name | TEXT | As per Aadhaar |
| email | TEXT UNIQUE | Login identifier |
| phone | TEXT | 10-digit mobile |
| aadhaar | TEXT UNIQUE | 12-digit Aadhaar |
| password_hash | TEXT | Werkzeug bcrypt |
| role | TEXT | citizen / admin / police |

### `applications`
| Column | Type | Notes |
|--------|------|-------|
| application_number | TEXT UNIQUE | Format: IND2025XXXXXXXX |
| user_id | FK → users | |
| status | TEXT | submitted → ml_verified → police_approved → issued |
| police_status | TEXT | pending / approved / rejected |
| admin_status | TEXT | pending / approved / rejected |
| passport_number | TEXT | Generated on issue (e.g. A1234567) |
| tatkaal | INTEGER | 0/1 — express service flag |

### `verification_logs`
| Column | Type | Notes |
|--------|------|-------|
| verification_type | TEXT | ml_auto / police_manual / admin_final |
| result | INTEGER | 0=fail, 1=pass |
| confidence_score | REAL | 0.0–1.0 overall ML score |
| face_match_score | REAL | Individual face check |
| document_validity_score | REAL | Document integrity check |
| aadhaar_match_score | REAL | UIDAI cross-validation |

### `documents`
Stores uploaded file metadata. Files saved to `uploads/` folder.

---

## 🤖 ML Verification Engine

Located in `app/ml_model.py`. The engine runs **automatically** after every application submission.

### Pipeline

```python
overall_score = (
    face_match_score      × 0.35  +   # DeepFace in production
    document_validity     × 0.30  +   # OCR + integrity check
    aadhaar_match_score   × 0.25  +   # UIDAI API in production
    address_verification  × 0.10      # India Post API in production
)
# Pass threshold: 0.65
```

### Extending to Real ML
```python
# Replace in ml_model.py:

# Face match → DeepFace
from deepface import DeepFace
result = DeepFace.verify(img1_path, img2_path)
face_score = result['distance']  # normalize to 0-1

# Aadhaar → UIDAI eKYC
import requests
response = requests.post('https://uidai.gov.in/verify', json={...})
aadhaar_score = 1.0 if response['status'] == 'valid' else 0.2

# Document OCR → Tesseract
import pytesseract
text = pytesseract.image_to_string(image_path)
doc_score = validate_extracted_text(text)
```

---

## 🔐 Security Features

- **Password hashing** via Werkzeug (bcrypt-equivalent PBKDF2)
- **Session management** — secure Flask sessions with secret key
- **Input sanitization** — `html.escape()` on all user inputs (XSS prevention)
- **Parameterized queries** — no string formatting in SQL (SQLi prevention)
- **Role-based access control** — `@role_required('admin')` decorators
- **File upload validation** — extension whitelist (pdf, jpg, png only)
- **5MB upload limit** enforced by Flask

---

## 🎨 UI Design

**Theme:** Indian government portal — tricolor (saffron #FF9933, white, green #138808), navy blue accents  
**Fonts:** Noto Serif (headings) + DM Sans (body) + JetBrains Mono (codes)  
**Components:** Card layouts, progress timelines, ML score bars, responsive tables

### Key Pages

| Page | Route | Description |
|------|-------|-------------|
| Home | `/` | Hero + passport card visual + stats + process flow |
| Login | `/auth/login` | Split-panel with demo credentials |
| Register | `/auth/register` | Full citizen registration |
| Apply | `/citizen/apply` | 4-step wizard with file upload |
| Dashboard | `/citizen/dashboard` | Application cards with progress bars |
| Track | `/track` | Public status lookup by application number |
| Police | `/police/dashboard` | ML results table + queue |
| Admin | `/admin/dashboard` | Analytics + filterable applications table |

---

## 📝 Application Status Flow

```
submitted → ml_verified ──────────────────┐
          → ml_failed ────► (still sent   │
                             to police)   │
                                          ▼
                               police_approved → issued ✅
                               police_rejected → ❌
                               admin_rejected  → ❌
```

---

## ⚠️ Disclaimer

This is an **educational/demonstration** project. It is **not affiliated** with the Government of India, Ministry of External Affairs, or any official body. All credentials, data, and passport numbers generated are entirely fictional and for demo purposes only.

---

*Built for learning full-stack development, ML integration, and government systems simulation.*
