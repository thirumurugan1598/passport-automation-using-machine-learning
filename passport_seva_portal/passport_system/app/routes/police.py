from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from app.database import DATABASE
from app.utils import role_required, sanitize_input

police_bp = Blueprint('police', __name__)

@police_bp.route('/dashboard')
@role_required('police')
def dashboard():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    applications = conn.execute("""
        SELECT a.*, u.full_name as citizen_name, u.email, u.phone,
               vl.confidence_score, vl.face_match_score, vl.document_validity_score,
               vl.aadhaar_match_score, vl.result as ml_result
        FROM applications a JOIN users u ON a.user_id = u.id
        LEFT JOIN (SELECT application_id, confidence_score, face_match_score,
                   document_validity_score, aadhaar_match_score, result
            FROM verification_logs WHERE id IN (SELECT MAX(id) FROM verification_logs GROUP BY application_id)
        ) vl ON a.id = vl.application_id
        WHERE a.status IN ('ml_verified','ml_failed','police_review')
        ORDER BY a.tatkaal DESC, a.created_at ASC
    """).fetchall()
    stats = {
        'pending': conn.execute("SELECT COUNT(*) as c FROM applications WHERE status IN ('ml_verified','ml_failed','police_review')").fetchone()['c'],
        'approved': conn.execute("SELECT COUNT(*) as c FROM applications WHERE police_status='approved'").fetchone()['c'],
        'rejected': conn.execute("SELECT COUNT(*) as c FROM applications WHERE police_status='rejected'").fetchone()['c'],
    }
    conn.close()
    return render_template('police/dashboard.html', applications=applications, stats=stats)

@police_bp.route('/review/<int:app_id>')
@role_required('police')
def review(app_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    application = conn.execute("""
        SELECT a.*, u.full_name as citizen_name, u.email, u.phone, u.aadhaar
        FROM applications a JOIN users u ON a.user_id=u.id WHERE a.id=?
    """, (app_id,)).fetchone()
    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('police.dashboard'))
    logs = conn.execute("SELECT * FROM verification_logs WHERE application_id=? ORDER BY verified_at DESC", (app_id,)).fetchall()
    documents = conn.execute("SELECT * FROM documents WHERE application_id=?", (app_id,)).fetchall()
    conn.close()
    return render_template('police/review.html', application=application, logs=logs, documents=documents)

@police_bp.route('/verify/<int:app_id>', methods=['POST'])
@role_required('police')
def verify(app_id):
    decision = request.form.get('decision')
    remarks = sanitize_input(request.form.get('remarks', ''))
    if decision not in ('approve','reject'):
        flash('Invalid decision.', 'danger')
        return redirect(url_for('police.review', app_id=app_id))
    new_status = 'police_approved' if decision == 'approve' else 'police_rejected'
    police_status = 'approved' if decision == 'approve' else 'rejected'
    conn = sqlite3.connect(DATABASE)
    conn.execute("""UPDATE applications SET status=?, police_status=?, police_remarks=?,
        police_officer_id=?, police_verified_at=CURRENT_TIMESTAMP WHERE id=?""",
        (new_status, police_status, remarks, session['user_id'], app_id))
    conn.execute("""INSERT INTO verification_logs (application_id, verification_type, result, confidence_score, details)
        VALUES (?, 'police_manual', ?, 1.0, ?)""",
        (app_id, 1 if decision=='approve' else 0, f"Police {decision}d. Remarks: {remarks}"))
    conn.commit()
    conn.close()
    flash(f'Application {"approved" if decision=="approve" else "rejected"} and forwarded to Admin.', 'success' if decision=='approve' else 'warning')
    return redirect(url_for('police.dashboard'))
