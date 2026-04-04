"""
ML Verification Module — Passport Automation System
Simulates a real-world ML document & face verification pipeline.
Extensible to real models (DeepFace, OpenCV, Tesseract OCR, UIDAI API, etc.)
"""
import random
import re
import os
import hashlib
import time
from datetime import datetime


class PassportMLVerifier:
    """
    Weighted ML ensemble for passport document verification.
    In production, replace methods with:
      - face_match()       → DeepFace / AWS Rekognition
      - validate_document() → Tesseract OCR + regex rules
      - aadhaar_verify()   → UIDAI eKYC API
    """
    def __init__(self):
        self.model_version = "v2.3.1"
        self.threshold = 0.65

    def face_match_score(self, name: str, photo_path: str = None) -> float:
        seed = int(hashlib.md5(name.encode()).hexdigest()[:8], 16)
        random.seed(seed + int(time.time()) % 100)
        if photo_path and os.path.exists(photo_path):
            return min(1.0, max(0.0, random.uniform(0.78, 0.99) + random.gauss(0, 0.02)))
        return min(1.0, max(0.0, random.uniform(0.70, 0.94) + random.gauss(0, 0.03)))

    def document_validity_score(self, applicant_data: dict) -> float:
        random.seed(int(time.time() * 100) % 9999)
        base = random.uniform(0.72, 0.97)
        completeness = sum(1 for v in applicant_data.values() if v) / max(len(applicant_data), 1)
        return min(1.0, base * (0.85 + 0.15 * completeness))

    def aadhaar_match_score(self, name: str, aadhaar: str, dob: str) -> float:
        aadhaar = str(aadhaar).strip().replace(' ', '')
        if len(aadhaar) == 12 and aadhaar.isdigit() and aadhaar[0] not in ('0','1'):
            hash_val = int(hashlib.sha256(f"{name}{aadhaar}{dob}".encode()).hexdigest()[:6], 16)
            random.seed(hash_val % 10000)
            return random.uniform(0.80, 0.98)
        return random.uniform(0.25, 0.50)

    def address_verification_score(self, pincode: str, city: str, state: str) -> float:
        score = 0.40
        if re.match(r'^\d{6}$', str(pincode).strip()): score += 0.25
        if city and len(city.strip()) >= 2: score += 0.20
        if state and len(state.strip()) >= 2: score += 0.15
        return min(1.0, score)

    def verify_document(self, application_data: dict, documents: list = None) -> dict:
        """
        Main verification pipeline — called automatically after application submission.
        Returns: result (bool), confidence_score, individual scores, details
        """
        name = application_data.get('applicant_name', '')
        aadhaar = application_data.get('aadhaar', '')
        dob = application_data.get('dob', '')
        pincode = application_data.get('pincode', '')
        city = application_data.get('city', '')
        state = application_data.get('state', '')

        photo_path = documents[0] if documents else None

        face_score      = self.face_match_score(name, photo_path)
        doc_score       = self.document_validity_score(application_data)
        aadhaar_score   = self.aadhaar_match_score(name, aadhaar, dob)
        addr_score      = self.address_verification_score(pincode, city, state)

        # Weighted ensemble
        weights = {'face': 0.35, 'doc': 0.30, 'aadhaar': 0.25, 'addr': 0.10}
        overall = (face_score * weights['face'] + doc_score * weights['doc'] +
                   aadhaar_score * weights['aadhaar'] + addr_score * weights['addr'])
        overall = round(min(1.0, max(0.0, overall)), 4)
        passed = overall >= self.threshold

        flags = []
        if face_score < 0.75: flags.append('Low face match confidence')
        if doc_score < 0.75:  flags.append('Document quality concern')
        if aadhaar_score < 0.70: flags.append('Aadhaar verification inconclusive')
        if not passed: flags.append('Manual police verification required')

        details = {
            'model_version': self.model_version,
            'threshold': self.threshold,
            'individual_scores': {
                'face_match': round(face_score * 100, 1),
                'document_validity': round(doc_score * 100, 1),
                'aadhaar_match': round(aadhaar_score * 100, 1),
                'address_verification': round(addr_score * 100, 1),
            },
            'flags': flags,
        }

        return {
            'result': passed,
            'confidence_score': overall,
            'face_match_score': round(face_score, 4),
            'document_validity_score': round(doc_score, 4),
            'aadhaar_match_score': round(aadhaar_score, 4),
            'address_verification_score': round(addr_score, 4),
            'details': str(details),
            'model_version': self.model_version,
            'verified_at': datetime.now().isoformat()
        }


_verifier = PassportMLVerifier()

def verify_document(application_data: dict, documents: list = None) -> dict:
    """Public API — called by citizen routes after application submission."""
    return _verifier.verify_document(application_data, documents)
