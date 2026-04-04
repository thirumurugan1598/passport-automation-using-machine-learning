from flask import Blueprint, render_template, request
import sqlite3
from app.database import DATABASE

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    stats = {
        'total_applications': conn.execute("SELECT COUNT(*) as c FROM applications").fetchone()['c'],
        'issued': conn.execute("SELECT COUNT(*) as c FROM applications WHERE status='issued'").fetchone()['c'],
        'processing': conn.execute("SELECT COUNT(*) as c FROM applications WHERE status NOT IN ('issued','rejected','admin_rejected','police_rejected')").fetchone()['c'],
    }
    conn.close()
    return render_template('main/index.html', stats=stats)

@main_bp.route('/track', methods=['GET', 'POST'])
def track():
    application = None
    logs = None
    if request.method == 'POST':
        app_number = request.form.get('application_number', '').strip().upper()
        if app_number:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            application = conn.execute(
                "SELECT a.*, u.full_name, u.email FROM applications a JOIN users u ON a.user_id=u.id WHERE a.application_number=?",
                (app_number,)
            ).fetchone()
            if application:
                logs = conn.execute(
                    "SELECT * FROM verification_logs WHERE application_id=? ORDER BY verified_at DESC",
                    (application['id'],)
                ).fetchall()
            conn.close()
    return render_template('main/track.html', application=application, logs=logs)
