#!/usr/bin/env python3
"""
Passport Seva Portal — Run Script
Government of India (Demo/Educational System)
"""
import sys
import os

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask
except ImportError:
    print("❌ Flask not found. Run: pip install flask werkzeug")
    sys.exit(1)

import importlib.util
spec = importlib.util.spec_from_file_location('main_app', os.path.join(os.path.dirname(__file__), 'app.py'))
main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_mod)
app = main_mod.create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*55)
    print("  🇮🇳  PASSPORT SEVA PORTAL — STARTING UP")
    print("="*55)
    print(f"  🌐  http://localhost:{port}")
    print(f"  🛡️  Admin:  admin@passport.gov.in / Admin@123")
    print(f"  👮  Police: police@passport.gov.in / Police@123")
    print(f"  👤  Citizen: Register at /auth/register")
    print("="*55 + "\n")
    app.run(debug=True, host='0.0.0.0', port=port)
