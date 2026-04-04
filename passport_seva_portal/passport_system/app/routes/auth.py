from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from app.database import DATABASE
from app.utils import (sanitize_input, validate_email, validate_phone,
                       validate_aadhaar, validate_password)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('citizen.dashboard'))
    if request.method == 'POST':
        full_name = sanitize_input(request.form.get('full_name', ''))
        email = sanitize_input(request.form.get('email', '').lower())
        phone = sanitize_input(request.form.get('phone', ''))
        aadhaar = sanitize_input(request.form.get('aadhaar', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        errors = []
        if not full_name or len(full_name) < 3:
            errors.append("Full name must be at least 3 characters.")
        if not validate_email(email):
            errors.append("Invalid email address.")
        if not validate_phone(phone):
            errors.append("Invalid phone number (10 digits starting with 6-9).")
        if not validate_aadhaar(aadhaar):
            errors.append("Aadhaar must be exactly 12 digits.")
        pw_valid, pw_msg = validate_password(password)
        if not pw_valid:
            errors.append(pw_msg)
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html', form_data={'full_name': full_name, 'email': email, 'phone': phone})
        try:
            conn = sqlite3.connect(DATABASE)
            conn.execute("INSERT INTO users (full_name, email, phone, aadhaar, password_hash, role) VALUES (?, ?, ?, ?, ?, 'citizen')",
                (full_name, email, phone, aadhaar, generate_password_hash(password)))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError as e:
            if 'email' in str(e):
                flash('Email already registered.', 'danger')
            elif 'aadhaar' in str(e):
                flash('Aadhaar number already registered.', 'danger')
            else:
                flash('Registration failed. Please try again.', 'danger')
    return render_template('auth/register.html', form_data={})

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('role', 'citizen')
        return redirect(url_for('admin.dashboard' if role == 'admin' else 'police.dashboard' if role == 'police' else 'citizen.dashboard'))
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', '').lower())
        password = request.form.get('password', '')
        if not email or not password:
            flash('Please enter email and password.', 'danger')
            return render_template('auth/login.html')
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT * FROM users WHERE email=? AND is_active=1", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            session['role'] = user['role']
            session.permanent = True
            flash(f"Welcome back, {user['full_name']}!", 'success')
            role = user['role']
            if role == 'admin': return redirect(url_for('admin.dashboard'))
            elif role == 'police': return redirect(url_for('police.dashboard'))
            else: return redirect(url_for('citizen.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    full_name = session.get('full_name', 'User')
    session.clear()
    flash(f'Goodbye, {full_name}! You have been logged out.', 'info')
    return redirect(url_for('main.index'))
