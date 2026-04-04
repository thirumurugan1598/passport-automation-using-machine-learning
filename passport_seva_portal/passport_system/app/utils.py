import re
import html
from functools import wraps
from flask import session, redirect, url_for, flash


def sanitize_input(value: str) -> str:
    """Sanitize input to prevent XSS."""
    if value is None:
        return ''
    return html.escape(str(value).strip())


def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    return bool(re.match(r'^[6-9]\d{9}$', phone))


def validate_aadhaar(aadhaar: str) -> bool:
    return bool(re.match(r'^\d{12}$', aadhaar))


def validate_pincode(pincode: str) -> bool:
    return bool(re.match(r'^[1-9][0-9]{5}$', pincode))


def validate_password(password: str) -> tuple:
    """Returns (is_valid, error_message)"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, ""


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to continue.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') not in roles:
                flash('Access denied. Insufficient permissions.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def generate_application_number() -> str:
    """Generate a unique application number like IND2025XXXX."""
    import random, string
    from datetime import datetime
    year = datetime.now().year
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"IND{year}{suffix}"


def generate_passport_number() -> str:
    """Generate a passport number like A1234567."""
    import random, string
    letter = random.choice(string.ascii_uppercase)
    digits = ''.join(random.choices(string.digits, k=7))
    return f"{letter}{digits}"


ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
