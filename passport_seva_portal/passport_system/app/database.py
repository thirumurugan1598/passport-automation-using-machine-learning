import sqlite3
import os

DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'passport.db')

def get_db():
    conn = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL, phone TEXT NOT NULL, aadhaar TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'citizen',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, application_number TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL, applicant_name TEXT NOT NULL, dob TEXT NOT NULL,
            gender TEXT NOT NULL, address TEXT NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL,
            pincode TEXT NOT NULL, father_name TEXT NOT NULL, mother_name TEXT NOT NULL,
            spouse_name TEXT, nationality TEXT DEFAULT 'Indian', passport_type TEXT NOT NULL,
            tatkaal INTEGER DEFAULT 0, emergency_contact TEXT, existing_passport TEXT,
            status TEXT DEFAULT 'submitted', police_status TEXT DEFAULT 'pending',
            police_remarks TEXT, police_officer_id INTEGER, police_verified_at TIMESTAMP,
            admin_status TEXT DEFAULT 'pending', admin_remarks TEXT, admin_officer_id INTEGER,
            admin_approved_at TIMESTAMP, passport_number TEXT, passport_issued_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, application_id INTEGER NOT NULL,
            doc_type TEXT NOT NULL, file_path TEXT NOT NULL, original_filename TEXT NOT NULL,
            file_size INTEGER, mime_type TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS verification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, application_id INTEGER NOT NULL,
            verification_type TEXT NOT NULL, result INTEGER NOT NULL, confidence_score REAL NOT NULL,
            face_match_score REAL, document_validity_score REAL, aadhaar_match_score REAL,
            details TEXT, verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT NOT NULL,
            entity_type TEXT, entity_id INTEGER, ip_address TEXT, details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    from werkzeug.security import generate_password_hash
    if not cursor.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone():
        cursor.execute("INSERT INTO users (full_name,email,phone,aadhaar,password_hash,role) VALUES (?,?,?,?,?,'admin')",
            ('Admin Officer','admin@passport.gov.in','9000000001','100000000001',generate_password_hash('Admin@123')))
    if not cursor.execute("SELECT id FROM users WHERE role='police' LIMIT 1").fetchone():
        cursor.execute("INSERT INTO users (full_name,email,phone,aadhaar,password_hash,role) VALUES (?,?,?,?,?,'police')",
            ('Police Officer','police@passport.gov.in','9000000002','100000000002',generate_password_hash('Police@123')))
    conn.commit()
    conn.close()
    print("✅ Database initialized.")
