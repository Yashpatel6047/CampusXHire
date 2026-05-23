<<<<<<< HEAD
# CampusXHire (Flask Web App) 🚀


CampusXHire is a Flask-based web application that supports student registration/login, job discovery & application, company/job-post management, and student profile management.

---

## Features

- Student registration with OTP verification
- Student login/logout
- Student profile update (personal details, resume/video resume uploads, portfolio link)
- Skill management (SQLAlchemy relationship)
- Job search + recommended jobs based on skill overlap
- Job application flow
- Admin dashboard pages (templates included)

---

## Tech Stack

- **Backend:** Flask
- **Database:** SQLite (see `instance/`)
- **ORM:** SQLAlchemy
- **Frontend:** HTML/Jinja templates + static CSS/JS

---

## Project Structure (high level)

- `run.py` - app entrypoint
- `app/` - Flask app package
  - `routes/` - route handlers
  - `models/` - SQLAlchemy models
  - `controllers/` - app controllers
  - `extensions/` - shared extensions (db/mail, etc.)
  - `templates/` - Jinja templates
  - `static/` - static assets and uploads
- `instance/` - SQLite database files

---

## Setup & Run Locally

### 1) Create & activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
```

### 2) Install dependencies
=======
# 🚀 CampusXHire – Flask Recruitment Platform

CampusXHire is a **Flask-based recruitment web application** designed to connect **students** with **companies** through a streamlined hiring process.  
The platform supports student registration, profile management, job discovery, applications, and company-side job posting.

---

## ✨ Features

### 👨‍🎓 Student Module
✅ Student registration with OTP verification  
✅ Secure login/logout  
✅ Profile creation & updates  
✅ Resume upload  
✅ Video resume upload  
✅ Portfolio/GitHub/LinkedIn links  
✅ Skill management using SQLAlchemy relationships  
✅ Personalized job recommendations based on skill matching  
✅ Job application tracking  

### 🏢 Company/Admin Module
✅ Post new job opportunities  
✅ Manage active job listings  
✅ View applicants  
✅ Dashboard pages for administration  
✅ Edit/Delete job postings  

---

## 🛠 Tech Stack

| Technology | Usage |
|------------|--------|
| Python | Core programming |
| Flask | Backend framework |
| SQLite | Database |
| SQLAlchemy | ORM |
| HTML5 | Frontend structure |
| CSS3 | Styling |
| JavaScript | Client-side interaction |
| Jinja2 | Template engine |

---

## 📂 Project Structure

```bash
CampusXHire/
│
├── run.py                     # Application entry point
│
├── app/
│   ├── routes/               # Route handlers
│   ├── models/               # Database models
│   ├── controllers/          # Business logic
│   ├── extensions/           # Shared extensions
│   ├── templates/            # HTML templates
│   ├── static/               # CSS, JS, uploads
│
├── instance/                 # SQLite database
│
├── requirements.txt          # Dependencies
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone <your-repository-url>
cd CampusXHire
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

### 3️⃣ Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / Mac

```bash
source venv/bin/activate
```

### 4️⃣ Install Dependencies
>>>>>>> b023fec76e75c42427dcf036c1095c4f5b566ffd

```bash
pip install -r requirements.txt
```

<<<<<<< HEAD
### 3) Configure environment

This project uses configuration under `app/config/`.

If the app expects a database, make sure `instance/campusxhire.db` exists (it is included in the repo).

### 4) Run the application
=======
---

## ▶️ Run the Application
>>>>>>> b023fec76e75c42427dcf036c1095c4f5b566ffd

```bash
python run.py
```

<<<<<<< HEAD
Then open:

- http://127.0.0.1:5000

---

## Uploads

Uploads are stored under `app/static/uploads/` (and subfolders such as resumes/photos/video_resumes).

---

## Notes

### Fix included for skills relationship

While updating a student profile, the app correctly handles the SQLAlchemy relationship for `student.skills` by reading a list from the form (`request.form.getlist("skills")`) and updating the relationship collection.

---

## Deployment

For production, use a WSGI server such as **gunicorn** (Linux) or **waitress** (Windows). Do not use Flask’s built-in server.

---

## License

Add your license here (e.g., MIT). 

=======
Application will start at:

```bash
http://127.0.0.1:5000
```

---

## 📤 Upload Management

Uploaded files are stored in:

```bash
app/static/uploads/
```

Supported uploads:

📄 Resume files  
🎥 Video resumes  
🖼 Profile photos  
🔗 Portfolio links  

---

## 🧠 Smart Recommendation System

CampusXHire recommends jobs by matching:

✅ Student skills  
✅ Job requirements  
✅ Skill overlap percentage  

This improves relevant job discovery for students.

---

## 🔧 Database

Default database:

```bash
instance/campusxhire.db
```

ORM used:

**SQLAlchemy**

---

## 🐞 Important Fixes Implemented

### Skill Relationship Fix

Student skills are updated correctly using:

```python
request.form.getlist("skills")
```

This ensures proper SQLAlchemy relationship handling.

---

## 🚀 Deployment

For production deployment, use:

### Linux

- Gunicorn

### Windows

- Waitress

⚠️ Flask development server should not be used in production.

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository  
2. Create your feature branch  
3. Commit your changes  
4. Push to branch  
5. Open a Pull Request  

---

## 👩‍💻 Developed By

**Saloni Gorsiya**  
Computer Engineering Student  
**Jehan Musabji**
Computer Engineering Student 
**Yash Oganja**
Computer Engineering Student 
---

## 📜 License

This project is licensed under the **MIT License**.

---

⭐ If you like this project, don't forget to star the repository.
>>>>>>> b023fec76e75c42427dcf036c1095c4f5b566ffd
