from flask import Flask, render_template, request, jsonify, redirect
import os
import qrcode
import validators
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from models.qr_model import db, QRCode

app = Flask(__name__)

# ==========================
# CONFIG
# ==========================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# 🚨 FIXED: MUST BE RENDER URL ONLY
BASE_URL = "https://qrverse-pgco.onrender.com"

QR_FOLDER = os.path.join("static", "qr_codes")
os.makedirs(QR_FOLDER, exist_ok=True)

# ==========================
# HELPERS
# ==========================

def normalize_url(value):
    value = value.strip()

    if value and "." in value and not value.startswith(("http://", "https://")):
        return "https://" + value

    return value


def detect_input_type(data):
    try:
        validate_email(data)
        return "Email"
    except:
        pass

    if validators.url(data):
        return "URL"

    return "Text"


def format_qr_data(data, action):
    raw = data.strip()

    if action == "call":
        return f"tel:+91{raw}"
    elif action == "sms":
        return f"SMSTO:+91{raw}:"
    elif action == "whatsapp":
        return f"https://wa.me/91{raw}"
    elif action == "email":
        return f"mailto:{raw}"

    return normalize_url(raw)

# ==========================
# HOME
# ==========================

@app.route("/")
def home():
    qrs = QRCode.query.order_by(QRCode.created_at.desc()).all()
    return render_template("index.html", qrs=qrs)

# ==========================
# QR GENERATION (FIXED)
# ==========================

@app.route("/live-preview", methods=["POST"])
def live_preview():

    data = request.get_json()

    user_input = data.get("qrdata", "")
    action = data.get("action", "website")

    if not user_input:
        return jsonify({"error": "No input"})

    formatted = format_qr_data(user_input, action)

    qr_entry = QRCode.query.filter_by(original_data=formatted).first()

    if not qr_entry:
        qr_entry = QRCode(
            original_data=formatted,
            qr_type=detect_input_type(user_input),
            scans=0,
            last_scanned=None
        )
        db.session.add(qr_entry)
        db.session.commit()

    # 🚨 CRITICAL FIX: ALWAYS USE RENDER URL
    dynamic_url = f"{BASE_URL}/r/{qr_entry.short_id}"

    qr = qrcode.make(dynamic_url)

    filename = f"{qr_entry.short_id}.png"
    filepath = os.path.join(QR_FOLDER, filename)

    qr.save(filepath)

    return jsonify({
        "qr_image": f"static/qr_codes/{filename}",
        "dynamic_url": dynamic_url
    })

# ==========================
# REDIRECT (SAFE FIXED)
# ==========================

@app.route("/r/<short_id>")
def redirect_qr(short_id):

    qr_entry = QRCode.query.filter_by(short_id=short_id).first()

    if not qr_entry:
        return "<h1>QR Not Found</h1>"

    qr_entry.scans += 1
    qr_entry.last_scanned = datetime.utcnow()
    db.session.commit()

    data = qr_entry.original_data.strip()

    if data.startswith("http://") or data.startswith("https://"):
        return redirect(data, code=302)

    if data.startswith("mailto:") or data.startswith("tel:"):
        return redirect(data, code=302)

    return f"""
    <h2>QR Content</h2>
    <p>{data}</p>
    <p><b>No redirect available</b></p>
    """

# ==========================
# DELETE QR
# ==========================

@app.route("/delete/<short_id>")
def delete_qr(short_id):

    qr = QRCode.query.filter_by(short_id=short_id).first()

    if not qr:
        return "<h1>QR Not Found</h1>"

    img_path = os.path.join(QR_FOLDER, f"{qr.short_id}.png")

    if os.path.exists(img_path):
        os.remove(img_path)

    db.session.delete(qr)
    db.session.commit()

    return "<script>alert('Deleted');window.location.href='/'</script>"

# ==========================
# START (RENDER SAFE)
# ==========================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)