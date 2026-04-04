import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.utils import secure_filename
import sqlite3
from app.database import DATABASE
from app.utils import (login_required, role_required, sanitize_input,
                       generate_application_number, allowed_file)
from app.ml_model import verify_document

citizen_bp = Blueprint('citizen', __name__)

@citizen_bp.route('/dashboard')
@role_required('citizen')
def dashboard():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    applications = conn.execute(
        "SELECT * FROM applications WHERE user_id=? ORDER BY created_at DESC",
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return render_template('citizen/dashboard.html', applications=applications)

@citizen_bp.route('/apply', methods=['GET', 'POST'])
@role_required('citizen')
def apply():
    if request.method == 'POST':
        f = request.form
        data = {
            'applicant_name': sanitize_input(f.get('applicant_name', '')),
            'dob': sanitize_input(f.get('dob', '')),
            'gender': sanitize_input(f.get('gender', '')),
            'address': sanitize_input(f.get('address', '')),
            'city': sanitize_input(f.get('city', '')),
            'state': sanitize_input(f.get('state', '')),
            'pincode': sanitize_input(f.get('pincode', '')),
            'father_name': sanitize_input(f.get('father_name', '')),
            'mother_name': sanitize_input(f.get('mother_name', '')),
            'spouse_name': sanitize_input(f.get('spouse_name', '')),
            'passport_type': sanitize_input(f.get('passport_type', '')),
            'tatkaal': 1 if f.get('tatkaal') else 0,
            'emergency_contact': sanitize_input(f.get('emergency_contact', '')),
            'existing_passport': sanitize_input(f.get('existing_passport', '')),
        }
        required = ['applicant_name','dob','gender','address','city','state','pincode','father_name','mother_name','passport_type']
        errors = [f"'{field.replace('_',' ').title()}' is required." for field in required if not data[field]]
        if data['pincode'] and (not data['pincode'].isdigit() or len(data['pincode']) != 6):
            errors.append("Please enter a valid 6-digit pincode.")
        if errors:
            for e in errors: flash(e, 'danger')
            return render_template('citizen/apply.html', form_data=data)

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
        data['aadhaar'] = user['aadhaar']

        upload_folder = current_app.config['UPLOAD_FOLDER']
        uploaded_docs = []
        for doc_field in ['photo','aadhaar_doc','address_proof','birth_certificate']:
            if doc_field in request.files:
                file = request.files[doc_field]
                if file and file.filename and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    unique_name = f"{uuid.uuid4().hex}.{ext}"
                    filepath = os.path.join(upload_folder, unique_name)
                    file.save(filepath)
                    uploaded_docs.append({'doc_type': doc_field, 'file_path': filepath,
                        'original_filename': secure_filename(file.filename),
                        'file_size': os.path.getsize(filepath), 'mime_type': file.content_type})

        app_number = generate_application_number()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (application_number, user_id, applicant_name, dob, gender,
                address, city, state, pincode, father_name, mother_name, spouse_name,
                passport_type, tatkaal, emergency_contact, existing_passport, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'submitted')
        """, (app_number, session['user_id'], data['applicant_name'], data['dob'], data['gender'],
              data['address'], data['city'], data['state'], data['pincode'], data['father_name'],
              data['mother_name'], data['spouse_name'], data['passport_type'], data['tatkaal'],
              data['emergency_contact'], data['existing_passport']))
        application_id = cursor.lastrowid

        for doc in uploaded_docs:
            cursor.execute("""INSERT INTO documents (application_id, doc_type, file_path, original_filename, file_size, mime_type)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (application_id, doc['doc_type'], doc['file_path'], doc['original_filename'], doc['file_size'], doc['mime_type']))
        conn.commit()

        ml_result = verify_document(data, [d['file_path'] for d in uploaded_docs])
        ml_passed = ml_result['result']
        new_status = 'ml_verified' if ml_passed else 'ml_failed'

        cursor.execute("""INSERT INTO verification_logs
            (application_id, verification_type, result, confidence_score, face_match_score, document_validity_score, aadhaar_match_score, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (application_id, 'ml_auto', 1 if ml_passed else 0, ml_result['confidence_score'],
             ml_result['face_match_score'], ml_result['document_validity_score'], ml_result['aadhaar_match_score'], ml_result['details']))
        cursor.execute("UPDATE applications SET status=? WHERE id=?", (new_status, application_id))
        conn.commit()
        conn.close()

        flash(f'Application submitted! Number: <strong>{app_number}</strong>. ML Verification: {"✅ Passed" if ml_passed else "⚠️ Under Review"}', 'success')
        return redirect(url_for('citizen.dashboard'))
    return render_template('citizen/apply.html', form_data={})

@citizen_bp.route('/application/<int:app_id>')
@role_required('citizen')
def view_application(app_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    application = conn.execute("SELECT * FROM applications WHERE id=? AND user_id=?", (app_id, session['user_id'])).fetchone()
    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('citizen.dashboard'))
    documents = conn.execute("SELECT * FROM documents WHERE application_id=?", (app_id,)).fetchall()
    logs = conn.execute("SELECT * FROM verification_logs WHERE application_id=? ORDER BY verified_at DESC", (app_id,)).fetchall()
    conn.close()
    return render_template('citizen/view_application.html', application=application, documents=documents, logs=logs)
