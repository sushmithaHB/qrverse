from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect
)

import os
import qrcode
import validators

from datetime import datetime

from email_validator import (
    validate_email
)

from models.qr_model import (
    db,
    QRCode
)

# ====================================
# APP CONFIG
# ====================================

app = Flask(__name__)

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "sqlite:///database.db"

app.config[
    "SQLALCHEMY_TRACK_MODIFICATIONS"
] = False

db.init_app(app)

# ====================================
# QR STORAGE
# ====================================

QR_FOLDER = os.path.join(
    "static",
    "qr_codes"
)

os.makedirs(
    QR_FOLDER,
    exist_ok=True
)

# ====================================
# NORMALIZE URL
# ====================================

def normalize_url(value):

    value = value.strip()

    if (
        "." in value and
        not value.startswith("http://") and
        not value.startswith("https://") and
        " " not in value
    ):

        return "https://" + value

    return value

# ====================================
# DETECT INPUT TYPE
# ====================================

def detect_input_type(data):

    raw = data.strip()

    lower = raw.lower()

    # PHONE

    cleaned = raw.replace(
        "+91",
        ""
    )

    if (
        cleaned.isdigit() and
        len(cleaned) == 10
    ):

        return "Phone Number"

    # EMAIL

    try:

        validate_email(raw)

        return "Email Address"

    except:

        pass

    # URL

    if validators.url(raw):

        if "youtube" in lower:

            return "YouTube"

        if "instagram" in lower:

            return "Instagram"

        if "wa.me" in lower:

            return "WhatsApp"

        return "Website"

    # WIFI

    if lower.startswith("wifi:"):

        return "WiFi"

    # UPI

    if lower.startswith("upi://"):

        return "UPI Payment"

    return "Plain Text"

# ====================================
# FORMAT QR DATA
# ====================================

def format_qr_data(
    data,
    action
):

    raw = data.strip()

    # CALL

    if action == "call":

        return f"tel:+91{raw}"

    # SMS

    elif action == "sms":

        return f"SMSTO:+91{raw}:"

    # WHATSAPP

    elif action == "whatsapp":

        return f"https://wa.me/91{raw}"

    # EMAIL

    elif action == "email":

        return f"mailto:{raw}"

    # WEBSITE

    return normalize_url(raw)

# ====================================
# HOME
# ====================================

@app.route("/")
def home():

    all_qrs = QRCode.query.order_by(

        QRCode.created_at.desc()

    ).all()

    total_qrs = QRCode.query.count()

    total_scans = sum(

        qr.scans

        for qr in all_qrs
    )

    recent_scans = QRCode.query.filter(

        QRCode.last_scanned != None

    ).order_by(

        QRCode.last_scanned.desc()

    ).limit(5).all()

    return render_template(

        "index.html",

        qrs=all_qrs,

        total_qrs=total_qrs,

        total_scans=total_scans,

        recent_scans=recent_scans
    )

# ====================================
# LIVE PREVIEW
# ====================================

@app.route(
    "/live-preview",
    methods=["POST"]
)
def live_preview():

    data = request.get_json()

    # ==========================
    # USER INPUT
    # ==========================

    user_input = data.get(
        "qrdata",
        ""
    )

    action = data.get(
        "action",
        "website"
    )

    # ==========================
    # DESIGN SETTINGS
    # ==========================

    qr_color = data.get(
        "qr_color",
        "#000000"
    )

    bg_color = data.get(
        "bg_color",
        "#ffffff"
    )

    qr_size = int(

        data.get(
            "qr_size",
            10
        )

    )

    # ==========================
    # VALIDATION
    # ==========================

    if not user_input:

        return jsonify({

            "error":
            "No input provided"

        })

    # ==========================
    # FORMAT DATA
    # ==========================

    formatted_data = format_qr_data(

        user_input,

        action

    )

    # ==========================
    # DETECT TYPE
    # ==========================

    qr_type = detect_input_type(
        user_input
    )

    # ==========================
    # CHECK EXISTING QR
    # ==========================

    qr_entry = QRCode.query.filter_by(

        original_data=formatted_data

    ).first()

    # ==========================
    # CREATE NEW QR
    # ==========================

    if not qr_entry:

        qr_entry = QRCode(

            original_data=formatted_data,

            qr_type=qr_type,

            scans=0,

            last_scanned=None

        )

        db.session.add(
            qr_entry
        )

        db.session.commit()

    # ==========================
    # DYNAMIC URL
    # =================================

    dynamic_url = (

        "http://192.168.1.7:5000/r/" +

        qr_entry.short_id

    )

    # ==========================
    # CREATE QR
    # ==========================

    qr = qrcode.QRCode(

        version=1,

        error_correction=
            qrcode.constants
            .ERROR_CORRECT_H,

        box_size=qr_size,

        border=4
    )

    qr.add_data(dynamic_url)

    qr.make(fit=True)

    # ==========================
    # APPLY COLORS
    # ==========================

    img = qr.make_image(

        fill_color=qr_color,

        back_color=bg_color

    )

    # ==========================
    # SAVE FILE
    # ==========================

    filename = (
        f"{qr_entry.short_id}.png"
    )

    filepath = os.path.join(

        QR_FOLDER,

        filename

    )

    img.save(filepath)

    # ==========================
    # RESPONSE
    # ==========================

    return jsonify({

        "qr_image":
            f"static/qr_codes/{filename}",

        "qr_type":
            qr_type,

        "dynamic_url":
            dynamic_url

    })

# ====================================
# REDIRECT QR
# ====================================

@app.route("/r/<short_id>")
def redirect_qr(short_id):

    qr_entry = QRCode.query.filter_by(

        short_id=short_id

    ).first()

    if not qr_entry:

        return """

        <h1>
            QR Not Found
        </h1>

        """

    # TRACK SCANS

    qr_entry.scans += 1

    qr_entry.last_scanned = (
        datetime.utcnow()
    )

    db.session.commit()

    return redirect(
        qr_entry.original_data
    )

# ====================================
# DELETE QR
# ====================================

@app.route("/delete/<short_id>")
def delete_qr(short_id):

    qr_entry = QRCode.query.filter_by(

        short_id=short_id

    ).first()

    if not qr_entry:

        return "<h1>QR Not Found</h1>"

    # DELETE IMAGE

    image_path = os.path.join(

        QR_FOLDER,

        f"{qr_entry.short_id}.png"

    )

    if os.path.exists(image_path):

        os.remove(image_path)

    db.session.delete(
        qr_entry
    )

    db.session.commit()

    return """

    <script>

        alert("QR Deleted!");

        window.location.href="/";

    </script>

    """

# ====================================
# START SERVER
# ====================================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )