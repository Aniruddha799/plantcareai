# Product Requirements Document (PRD)
## PlantCare AI — Plant Disease Detection & Recovery Tracking System

| | |
|---|---|
| **Version** | 1.0 |
| **Status** | Draft |
| **Owner** | Aniruddha |
| **Last Updated** | 08 Aug 2026 |
| **Document Type** | College Mini-Project PRD |

---

## 1. Executive Summary

PlantCare AI ek AI/ML-based web application hai jo farmer ko plant/leaf ki photo upload karne dega, disease identify karega, severity batayega, basic care tips dega, aur **sabse important — same plant ki future photos se uski recovery/condition trend (Improving / Stable / Worsening) track karega.**

Sirf ek baar disease detect karke chhod dena — ye bahut projects karte hain. Iska USP hai **time-series recovery tracking**, jo isse ek "diagnosis tool" se ek "plant health monitoring system" bana deta hai.

> **One-line pitch:** "Hamare system mein sirf disease detect nahi hoti, balki same plant ki previous aur current reports compare karke uski condition improve ho rahi hai ya worsen ho rahi hai, ye bhi track hota hai."

---

## 2. Problem Statement

Farmers ko plant disease early stage par identify karna difficult hota hai, aur jab identify ho bhi jaye:

- Unke paas plant ki **previous condition ka koi record nahi hota**
- Treatment effective ho raha hai ya nahi — ye judge karna guesswork ban jaata hai
- Same disease baar-baar treat karte rehte hain bina ye jaane ki condition actually improve ho rahi hai ya worsen

**Current (broken) farmer workflow:**
```
Plant mein problem → Photo dekhi → Guess kiya → Treatment/care → Kuch din baad phir check (no record)
```

**Proposed workflow:**
```
Photo → AI Disease Detection → Severity → Care Tips → Save Report → Future Photo → Recovery Trend
```

---

## 3. Goals & Objectives

### 3.1 Primary Goals
1. Leaf image se disease automatically detect karna (CNN-based classifier)
2. Disease ki severity classify karna (Mild / Moderate / Severe)
3. Disease-specific basic care tips provide karna
4. Plant-wise history maintain karna (Plant ID based tracking)
5. Time ke saath severity compare karke recovery trend calculate karna (Improving/Stable/Worsening)

### 3.2 Non-Goals (Explicitly Out of Scope for v1)
- Weather API integration
- Gemini / any LLM-based chatbot advice
- IoT sensors / automatic irrigation
- Pesticide/chemical dosage recommendations
- Native mobile app
- Multi-language support (v1 English/Hinglish UI only)
- Affected-area percentage / image segmentation

### 3.3 Success Metrics
| Metric | Target |
|---|---|
| Disease classification accuracy | ≥ 85% on test set |
| Precision / Recall / F1 | ≥ 85% each |
| API response time (`/predict`) | < 3 seconds |
| End-to-end demo flow (register → 3 scans → recovery trend) | Fully functional for viva |
| Model classes supported (v1) | 4 (Healthy, Early Blight, Late Blight, Bacterial Spot) |

---

## 4. Target Users / Personas

**Persona: Ramesh Patil (Primary)**
- Small-scale tomato/potato farmer, based in Nashik
- Owns a smartphone, basic digital literacy
- Wants quick, simple answers: "What's wrong with my plant, and is it getting better?"
- Not interested in complex dashboards or technical jargon

**Persona: Agriculture Student / Evaluator (Secondary — for viva/demo)**
- College professor / examiner evaluating the ML pipeline, architecture, and DB design

---

## 5. User Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-1 | Farmer | Register and log in securely | I can access my personal plant records |
| US-2 | Farmer | Add a new plant with crop name | The system tracks each plant separately |
| US-3 | Farmer | Upload a leaf photo | I can find out what disease my plant has |
| US-4 | Farmer | See the disease + confidence score | I know how reliable the prediction is |
| US-5 | Farmer | See severity level | I understand how serious the problem is |
| US-6 | Farmer | Get basic care tips | I know what immediate steps to take |
| US-7 | Farmer | See past reports for a plant | I can review history |
| US-8 | Farmer | See a recovery trend/graph | I know if my plant is improving or not |
| US-9 | Farmer | View dashboard summary | I get an overview of all my plants at a glance |

---

## 6. Complete System Workflow

```
                 🌱 PLANTCARE AI
                       │
                       ▼
                👨‍🌾 REGISTER / LOGIN
                       │
                       ▼
                  DASHBOARD
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       🌱 Add Plant         📋 History
             │
             ▼
       📸 Upload Leaf Photo
             │
             ▼
       Image Preprocessing (resize, normalize)
             │
             ▼
       🤖 TensorFlow/Keras CNN
             │
       ┌─────┴─────────────┐
       ▼                   ▼
   🦠 Disease          📊 Severity
       │                   │
       └─────────┬─────────┘
                 ▼
          💡 Care Tips
                 │
                 ▼
          💾 Save Report to DB
                 │
                 ▼
        📈 Recovery Trend Calculation
                 │
                 ▼
       Improving / Stable / Worsening
```

---

## 7. Functional Requirements

### 7.1 Authentication Module
- **FR-1:** System register form accept kare: Name, Email, Password, Location
- **FR-2:** Email unique honi chahiye (DB-level constraint)
- **FR-3:** Password kabhi plain text mein store nahi hoga — bcrypt/argon2 hashing use hogi
- **FR-4:** Login `email + password` se ho, JWT token issue ho successful login par
- **FR-5:** Protected routes (dashboard, upload, history, recovery) sirf valid JWT ke saath accessible hon
- **FR-6 (recommended addition):** Basic input validation — invalid email format, weak password (min 8 chars) reject ho

### 7.2 Plant Management Module
- **FR-7:** Farmer ek ya multiple plants add kar sake (crop_name + plant_name)
- **FR-8:** Har plant ko unique Plant ID (e.g., P001) auto-assign ho
- **FR-9:** Farmer apne saare plants ki list dekh sake
- **FR-10 (recommended addition):** Plant delete/archive karne ka option (soft delete recommended, taaki historical reports intact rahein)

### 7.3 Image Upload & Disease Detection Module
- **FR-11:** Farmer ek plant select karke uske liye leaf image upload kare
- **FR-12:** System sirf valid image formats accept kare (.jpg, .jpeg, .png)
- **FR-13:** Max file size limit enforce ho (e.g., 5MB) — invalid/corrupt files reject
- **FR-14:** Image preprocessing: resize to 224×224, normalize (pixel/255.0)
- **FR-15:** CNN model image classify kare 4 classes mein: Healthy, Early Blight, Late Blight, Bacterial Spot
- **FR-16:** Prediction ke saath confidence score (%) bhi return ho
- **FR-17 (recommended addition):** Agar top prediction confidence bahut low ho (e.g., < 40%), system "Uncertain — please retake photo with better lighting/focus" jaisa fallback message de, galat confident diagnosis avoid karne ke liye

### 7.4 Severity Detection Module
- **FR-18:** Disease detect hone ke baad system severity classify kare: Mild / Moderate / Severe
- **FR-19:** Har severity level ko numeric score assign ho: Mild=1, Moderate=2, Severe=3
- **FR-20:** Agar labelled severity dataset available na ho to MVP-friendly approach use ho (e.g., rule-based heuristic ya separate lightweight classifier — annotated subset se train)

### 7.5 Care Tips Module
- **FR-21:** Har disease ke liye predefined, static, general (non-chemical-dosage) care tips dikhaye jayein
- **FR-22:** Severe cases mein tip include ho: "Consult a local agriculture expert"

### 7.6 Recovery Tracking Module (⭐ Core USP)
- **FR-23:** Same Plant ID ki multiple reports ko chronologically DB mein store kiya jaye
- **FR-24:** Naya scan hone par system automatically previous report (same plant_id, same/related disease) fetch kare
- **FR-25:** Severity scores compare karke trend calculate ho:
  - `current_score < previous_score` → **Improving**
  - `current_score > previous_score` → **Worsening**
  - `current_score == previous_score` → **Stable**
- **FR-26:** Pehle scan ke case mein (no previous report) trend = "Baseline" / "First Scan" dikhaya jaye
- **FR-27:** Recovery history ko line/bar chart ke roop mein visualize kiya jaye (Chart.js)

### 7.7 Reporting & History Module
- **FR-28:** Farmer apne saare past reports (date, crop, disease, severity) dekh sake, plant-wise filter ke saath
- **FR-29:** Individual report detail view available ho (image, disease, severity, confidence, tips, trend)

### 7.8 Dashboard Module
- **FR-30:** Summary cards: total plants, total scans, diseases detected, plants improving
- **FR-31:** Recent reports table (last 3-5 scans)
- **FR-32:** Quick-action buttons: "Add New Plant", "Scan Plant"

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | `/predict` endpoint response < 3s for a single image on standard hardware |
| **Scalability** | v1 single-server deployment sufficient; DB schema designed to scale to multiple farmers/plants |
| **Security** | Passwords hashed (bcrypt); JWT-based auth; image upload validated against MIME-type spoofing |
| **Usability** | Simple, minimal UI — Bootstrap-based, mobile-responsive (farmers likely use phones) |
| **Reliability** | Graceful error handling — invalid image, model failure, DB failure sab par user-friendly error messages |
| **Data Privacy** | Uploaded leaf images sirf uploading farmer ko visible hon; koi image dusre farmer ko na dikhe |
| **Maintainability** | Modular FastAPI routers (auth, plants, prediction, reports); ML model decoupled via `ml/model.py` |
| **Portability** | SQLite for local dev/demo; MySQL-compatible schema for production-style setup |

---

## 9. System Architecture

```
┌─────────────────────────────┐
│         FRONTEND            │
│ HTML + CSS + Bootstrap + JS │
└──────────────┬──────────────┘
               │ HTTP/REST (JSON)
               ▼
┌─────────────────────────────┐
│          FASTAPI             │
│ Authentication (JWT)         │
│ Image Upload Handling        │
│ API Endpoints / Routers      │
│ Business Logic (recovery)    │
└───────┬─────────────┬───────┘
        │              │
        ▼              ▼
┌──────────────┐  ┌────────────────┐
│ TensorFlow/  │  │ MySQL / SQLite │
│ Keras CNN    │  │ Database       │
│ Model        │  │ (SQLAlchemy)   │
└──────────────┘  └────────────────┘
```

**Request Flow for `/predict`:**
```
Frontend → POST /predict (plant_id + image)
   → FastAPI receives & validates image
   → Image preprocessing (resize 224x224, normalize)
   → TensorFlow/Keras model inference
   → Disease + confidence output
   → Severity classification
   → Fetch previous report for same plant_id
   → Recovery trend calculation
   → Fetch static care tips for predicted disease
   → Save report + recovery record to DB
   → Return JSON response to frontend
```

---

## 10. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Bootstrap, JavaScript |
| Backend | Python + FastAPI |
| AI/ML | TensorFlow + Keras (CNN) |
| Image Processing | OpenCV / Pillow |
| Database | MySQL (production-style) / SQLite (dev/demo) |
| ORM | SQLAlchemy |
| Authentication | JWT + password hashing (bcrypt) |
| Charts | Chart.js |
| API Testing | Swagger UI (auto via FastAPI) / Postman |
| Model Serving | Loaded via Keras `.h5` file at FastAPI startup (in-memory) |

---

## 11. Database Design

### 11.1 Entity Relationship
```
FARMER (1) ──< PLANTS (Many)
PLANTS (1) ──< DISEASE_REPORTS (Many)
DISEASE_REPORTS (1) ──< RECOVERY_RECORDS (1)
```

### 11.2 Table Schemas

**`farmers`**
| Column | Type | Notes |
|---|---|---|
| id | Integer, PK | Auto-increment |
| name | String | Required |
| email | String, Unique | Required |
| password_hash | String | bcrypt hashed |
| location | String | Optional |
| created_at | DateTime | Default now |

**`plants`**
| Column | Type | Notes |
|---|---|---|
| id | Integer, PK | Auto-increment |
| farmer_id | Integer, FK → farmers.id | |
| crop_name | String | e.g., "Tomato" |
| plant_name | String | e.g., "Tomato Plant 1" |
| created_at | DateTime | Default now |
| is_active | Boolean | For soft-delete (recommended addition) |

**`disease_reports`**
| Column | Type | Notes |
|---|---|---|
| id | Integer, PK | Auto-increment |
| plant_id | Integer, FK → plants.id | |
| image_path | String | Stored file path |
| disease | String | Predicted class |
| severity | String | Mild/Moderate/Severe |
| confidence | Float | Model confidence (0-1) |
| tips | Text | JSON/serialized tips list |
| created_at | DateTime | Scan timestamp |

**`recovery_records`**
| Column | Type | Notes |
|---|---|---|
| id | Integer, PK | Auto-increment |
| plant_id | Integer, FK → plants.id | |
| report_id | Integer, FK → disease_reports.id | |
| severity_score | Integer | 1/2/3 |
| trend | String | Improving/Stable/Worsening/Baseline |
| created_at | DateTime | Default now |

> **Recommended addition:** ek `disease_info` static reference table/JSON file rakho jisme har disease ke liye default care tips stored hon, taaki tips hardcoded na hon backend logic mein — easier to update/extend.

---

## 12. API Specification

### 12.1 Authentication
**`POST /register`**
```json
Request: { "name": "Ramesh Patil", "email": "ramesh@gmail.com", "password": "********", "location": "Nashik" }
Response: { "farmer_id": 101, "message": "Registration successful" }
```

**`POST /login`**
```json
Request: { "email": "ramesh@gmail.com", "password": "********" }
Response: { "access_token": "jwt_token_here", "token_type": "bearer" }
```

### 12.2 Plant Management
**`POST /plants`** — Add new plant
```json
Request: { "crop_name": "Tomato", "plant_name": "Tomato Plant 1" }
Response: { "plant_id": "P001", "crop_name": "Tomato", "plant_name": "Tomato Plant 1" }
```
**`GET /plants`** — List all plants of logged-in farmer
**`GET /plants/{plant_id}`** — Get single plant detail

### 12.3 Disease Detection
**`POST /predict`**
```json
Request (multipart/form-data): plant_id=1, image=leaf.jpg
Response: {
  "disease": "Early Blight",
  "severity": "Moderate",
  "confidence": 0.88,
  "trend": "Improving",
  "tips": [
    "Remove/manage affected leaves",
    "Maintain proper airflow",
    "Monitor the plant regularly"
  ]
}
```

### 12.4 Reports
**`GET /reports`** — All reports for logged-in farmer (optionally filter by `plant_id`)
**`GET /reports/{report_id}`** — Single report detail

### 12.5 Recovery
**`GET /plants/{plant_id}/recovery`**
```json
Response: {
  "plant_id": "P001",
  "history": [
    { "date": "2026-08-01", "severity": "Severe", "score": 3 },
    { "date": "2026-08-05", "severity": "Moderate", "score": 2 },
    { "date": "2026-08-10", "severity": "Mild", "score": 1 }
  ],
  "overall_trend": "Improving"
}
```

---

## 13. Machine Learning Requirements

### 13.1 Dataset Structure
```
dataset/
├── Healthy/
├── Early_Blight/
├── Late_Blight/
└── Bacterial_Spot/
```
(PlantVillage dataset ya similar publicly available leaf disease dataset recommended for v1)

### 13.2 Preprocessing Pipeline
```
Original Image → Resize (224×224) → Normalize (pixel/255.0) → Model Input
```

### 13.3 Model
- Architecture: CNN (custom, ya transfer learning — MobileNetV2/ResNet base recommended for better accuracy with limited dataset/time — **recommended addition** over training from scratch)
- Train/Validation/Test split: 70/15/15
- Output: `plant_disease_model.h5`

### 13.4 Evaluation Metrics (mandatory — report actual numbers post-training, not assumed)
- Accuracy
- Precision
- Recall
- F1-score
- Confusion Matrix

### 13.5 Severity Classification Approach
- If labelled severity data available: separate lightweight classifier (image → severity)
- Else (MVP-friendly): rule-based heuristic using model's class-confidence spread or a small manually-annotated subset

---

## 14. UI / Page List

| Route | Purpose |
|---|---|
| `/login` | Farmer login |
| `/register` | Farmer registration |
| `/dashboard` | Summary + quick actions |
| `/plants` | List/add plants |
| `/upload` | Upload leaf photo for scan |
| `/result` | Show disease, severity, confidence, trend, tips |
| `/history` | All past reports, filterable |
| `/recovery` | Severity trend graph per plant |

*(Wireframe sketches already captured in the source planning doc — dashboard, upload, result, history, recovery pages.)*

---

## 15. Folder Structure

```
plantcare-ai/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   ├── plants.py
│   │   ├── prediction.py
│   │   └── reports.py
│   │
│   ├── ml/
│   │   ├── model.py
│   │   └── plant_disease_model.h5
│   │
│   ├── utils/
│   │   ├── preprocessing.py
│   │   └── recovery.py
│   │
│   └── uploads/
│
├── frontend/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── upload.html
│   ├── result.html
│   ├── history.html
│   ├── recovery.html
│   ├── css/
│   └── js/
│
├── dataset/
│   ├── Healthy/
│   ├── Early_Blight/
│   ├── Late_Blight/
│   └── Bacterial_Spot/
│
└── requirements.txt
```

---

## 16. MVP Scope (Must-Have for v1)

✅ Register/Login (with password hashing)
✅ Add Plant
✅ Upload Leaf Photo
✅ AI Disease Detection (4 classes)
✅ Severity Detection
✅ Basic Care Tips
✅ Save Report to DB
✅ History View
✅ Recovery/Condition Trend Tracking
✅ FastAPI REST API (documented via Swagger)
✅ Database (SQLite/MySQL)

**Explicitly excluded from v1:** Weather API, Gemini/LLM API, IoT sensors, automatic irrigation, chemical dosage recommendations, mobile app, multi-crop/multi-disease scale-up, image segmentation.

---

## 17. Future Roadmap (Post-MVP, Optional)

⭐ Multiple crops & more disease classes
⭐ PDF report export/download
⭐ Email notifications on new scan/report
⭐ Admin panel (view all farmers, plants, model performance)
⭐ Disease statistics/analytics (regional trends)
⭐ Affected-area percentage via image segmentation
⭐ Farmer-level analytics dashboard
⭐ Model retraining pipeline with new farmer-submitted images (active learning)

---

## 18. Risks & Assumptions

| Risk/Assumption | Mitigation |
|---|---|
| Severity-labelled dataset may not be available | Use rule-based/heuristic severity classification for MVP |
| Model accuracy dependent on dataset quality | Use a well-known public dataset (e.g., PlantVillage); document limitations honestly in viva |
| Low-confidence predictions could mislead farmer | Add confidence threshold + "uncertain, retake photo" fallback |
| Recovery trend assumes same disease across scans | Add logic: trend calculation valid only when disease label matches between consecutive reports for same plant |
| Farmer may upload unrelated/blurry images | Basic image validation (format, size); optionally a "is this a leaf?" pre-check if time permits |
| Legal/safety concern: AI is not a certified diagnosis | Explicit disclaimer on result page: "AI-based estimate, not a guaranteed medical/agricultural diagnosis" |

---

## 19. Suggested Timeline (College Project Pace)

| Phase | Duration | Deliverable |
|---|---|---|
| Phase 1 | Week 1-2 | DB schema, FastAPI skeleton, auth module |
| Phase 2 | Week 3-4 | Dataset prep, CNN model training, evaluation |
| Phase 3 | Week 5 | `/predict` API integration with trained model |
| Phase 4 | Week 6 | Severity logic + recovery trend calculation |
| Phase 5 | Week 7 | Frontend pages (Bootstrap) + Chart.js recovery graph |
| Phase 6 | Week 8 | Testing, bug fixes, documentation, viva prep |

---

## 20. Acceptance Criteria (Definition of Done for Demo)

- [ ] Farmer can register, log in, and stay authenticated via JWT
- [ ] Farmer can add at least 2 plants
- [ ] Farmer can upload a leaf image and receive disease + severity + confidence + tips
- [ ] A second scan on the same plant correctly shows trend (Improving/Stable/Worsening) compared to the first
- [ ] History page correctly lists all past reports
- [ ] Recovery page shows a working Chart.js graph of severity over time
- [ ] Model evaluation metrics (accuracy, precision, recall, F1, confusion matrix) documented with real numbers
- [ ] Swagger UI (`/docs`) shows all working endpoints

---

*End of PRD.*
