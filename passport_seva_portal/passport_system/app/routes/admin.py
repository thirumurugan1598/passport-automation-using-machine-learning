from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from app.database import DATABASE
from app.utils import role_required, sanitize_input, generate_passport_number

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    all_apps = conn.execute("""
        SELECT a.*, u.full_name as citizen_name, u.email,
               vl.confidence_score, vl.result as ml_result
        FROM applications a JOIN users u ON a.user_id = u.id
        LEFT JOIN (SELECT application_id, confidence_score, result FROM verification_logs
            WHERE id IN (SELECT MAX(id) FROM verification_logs GROUP BY application_id)
        ) vl ON a.id = vl.application_id
        ORDER BY a.tatkaal DESC, a.created_at ASC
    """).fetchall()
    stats = {
        'total': conn.execute("SELECT COUNT(*) as c FROM applications").fetchone()['c'],
        'pending_admin': conn.execute("SELECT COUNT(*) as c FROM applications WHERE status='police_approved'").fetchone()['c'],
        'issued': conn.execute("SELECT COUNT(*) as c FROM applications WHERE status='issued'").fetchone()['c'],
        'rejected': conn.execute("SELECT COUNT(*) as c FROM applications WHERE status IN ('rejected','admin_rejected','police_rejected')").fetchone()['c'],
        'in_progress': conn.execute("SELECT COUNT(*) as c FROM applications WHERE status NOT IN ('issued','rejected','admin_rejected','police_rejected')").fetchone()['c'],
        'tatkaal': conn.execute("SELECT COUNT(*) as c FROM applications WHERE tatkaal=1").fetchone()['c'],
        'citizens': conn.execute("SELECT COUNT(*) as c FROM users WHERE role='citizen'").fetchone()['c'],
    }
    conn.close()
    return render_template('admin/dashboard.html', applications=all_apps, stats=stats)

@admin_bp.route('/review/<int:app_id>')
@role_required('admin')
def review(app_id):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    application = conn.execute("""SELECT a.*, u.full_name as citizen_name, u.email, u.phone, u.aadhaar
        FROM applications a JOIN users u ON a.user_id=u.id WHERE a.id=?""", (app_id,)).fetchone()
    if not application:
        flash('Application not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    logs = conn.execute("SELECT * FROM verification_logs WHERE application_id=? ORDER BY verified_at DESC", (app_id,)).fetchall()
    documents = conn.execute("SELECT * FROM documents WHERE application_id=?", (app_id,)).fetchall()
    conn.close()
    return render_template('admin/review.html', application=application, logs=logs, documents=documents)

@admin_bp.route('/approve/<int:app_id>', methods=['POST'])
@role_required('admin')
def approve(app_id):
    decision = request.form.get('decision')
    remarks = sanitize_input(request.form.get('remarks', ''))
    if decision not in ('approve','reject'):
        flash('Invalid decision.', 'danger')
        return redirect(url_for('admin.review', app_id=app_id))
    conn = sqlite3.connect(DATABASE)
    if decision == 'approve':
        passport_number = generate_passport_number()
        conn.execute("""UPDATE applications SET status='issued', admin_status='approved', admin_remarks=?,
            admin_officer_id=?, admin_approved_at=CURRENT_TIMESTAMP,
            passport_number=?, passport_issued_at=CURRENT_TIMESTAMP WHERE id=?""",
            (remarks, session['user_id'], passport_number, app_id))
        conn.execute("""INSERT INTO verification_logs (application_id, verification_type, result, confidence_score, details)
            VALUES (?, 'admin_final', 1, 1.0, ?)""", (app_id, f"Passport issued. Number: {passport_number}. Remarks: {remarks}"))
        flash(f'✅ Passport issued! Number: {passport_number}', 'success')
    else:
        conn.execute("""UPDATE applications SET status='admin_rejected', admin_status='rejected', admin_remarks=?,
            admin_officer_id=?, admin_approved_at=CURRENT_TIMESTAMP WHERE id=?""",
            (remarks, session['user_id'], app_id))
        conn.execute("""INSERT INTO verification_logs (application_id, verification_type, result, confidence_score, details)
            VALUES (?, 'admin_final', 0, 1.0, ?)""", (app_id, f"Rejected by admin. Remarks: {remarks}"))
        flash('Application rejected.', 'warning')
    conn.commit()
    conn.close()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users')
@role_required('admin')
def users():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    all_users = conn.execute("""SELECT u.*, COUNT(a.id) as app_count FROM users u
        LEFT JOIN applications a ON u.id=a.user_id GROUP BY u.id ORDER BY u.created_at DESC""").fetchall()
    conn.close()
    return render_template('admin/users.html', users=all_users)
