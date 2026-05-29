from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file
)

from models.qr_model import db, QRCode

import os
import io

import qrcode
import qrcode.image.svg

from PIL import Image

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# =========================================
# DATABASE
# =========================================

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# =========================================
# QR FOLDER
# =========================================

QR_FOLDER = "static/qr_codes"

os.makedirs(QR_FOLDER, exist_ok=True)

# =========================================
# FORMAT QR DATA
# =========================================

def format_qr_data(data, action):

    raw = str(data).strip()

    # WEBSITE
    if action == "website":

        if raw.startswith("http://") or raw.startswith("https://"):

            return raw

        return "https://" + raw

    # WHATSAPP
    elif action == "whatsapp":

        number = raw.replace(" ", "").replace("+91", "")

        return f"https://wa.me/91{number}"

    # CALL
    elif action == "call":

        number = raw.replace(" ", "").replace("+91", "")

        return f"tel:+91{number}"

    # SMS
    elif action == "sms":

        number = raw.replace(" ", "").replace("+91", "")

        return f"SMSTO:+91{number}:"

    # EMAIL
    elif action == "email":

        return f"mailto:{raw}"

    # TEXT
    return raw

# =========================================
# CREATE QR IMAGE
# =========================================

def create_qr_image(
    data,
    fill_color,
    back_color,
    box_size
):

    qr = qrcode.QRCode(

        version=1,

        error_correction=qrcode.constants.ERROR_CORRECT_H,

        box_size=box_size,

        border=4
    )

    qr.add_data(data)

    qr.make(fit=True)

    img = qr.make_image(

        fill_color=fill_color,

        back_color=back_color

    ).convert("RGB")

    return img

# =========================================
# HOME
# =========================================

@app.route("/")
def home():

    qrs = QRCode.query.order_by(
        QRCode.created_at.desc()
    ).all()

    return render_template(
        "index.html",
        qrs=qrs
    )

# =========================================
# LIVE QR GENERATION
# =========================================

@app.route("/live-preview", methods=["POST"])
def live_preview():

    try:

        data = request.get_json()

        user_input = data.get(
            "qrdata",
            ""
        ).strip()

        action = data.get(
            "action",
            "website"
        )

        fill_color = data.get(
            "fill_color",
            "#000000"
        )

        back_color = data.get(
            "back_color",
            "#ffffff"
        )

        box_size = int(
            data.get(
                "box_size",
                10
            )
        )

        if not user_input:

            return jsonify({
                "error": "No input"
            })

        # FINAL QR CONTENT
        final_qr_data = format_qr_data(
            user_input,
            action
        )

        print("\n====================")
        print("QR CONTENT =", final_qr_data)
        print("====================\n")

        # SAVE DATABASE
        qr_entry = QRCode(

            original_data=final_qr_data,

            qr_type=action
        )

        db.session.add(qr_entry)

        db.session.commit()

        # CREATE QR IMAGE
        img = create_qr_image(

            final_qr_data,

            fill_color,

            back_color,

            box_size
        )

        filename = f"{qr_entry.short_id}.png"

        filepath = os.path.join(
            QR_FOLDER,
            filename
        )

        img.save(filepath)

        return jsonify({

            "qr_image":
            f"/static/qr_codes/{filename}",

            "dynamic_url":
            final_qr_data
        })

    except Exception as e:

        print("LIVE ERROR =", e)

        return jsonify({
            "error": str(e)
        })

# =========================================
# DOWNLOAD QR
# =========================================

@app.route("/download", methods=["POST"])
def download_qr():

    try:

        data = request.get_json()

        qrdata = data.get(
            "qrdata",
            ""
        ).strip()

        action = data.get(
            "action",
            "website"
        )

        file_format = data.get(
            "format",
            "jpeg"
        )

        fill_color = data.get(
            "fill_color",
            "#000000"
        )

        back_color = data.get(
            "back_color",
            "#ffffff"
        )

        box_size = int(
            data.get(
                "box_size",
                10
            )
        )

        final_qr_data = format_qr_data(
            qrdata,
            action
        )

        # =====================================
        # SVG
        # =====================================

        if file_format == "svg":

            factory = qrcode.image.svg.SvgImage

            img = qrcode.make(

                final_qr_data,

                image_factory=factory
            )

            img_io = io.BytesIO()

            img.save(img_io)

            img_io.seek(0)

            return send_file(

                img_io,

                mimetype="image/svg+xml",

                as_attachment=True,

                download_name="qr.svg"
            )

        # =====================================
        # NORMAL IMAGE QR
        # =====================================

        img = create_qr_image(

            final_qr_data,

            fill_color,

            back_color,

            box_size
        )

        img_io = io.BytesIO()

        # =====================================
        # PNG
        # =====================================

        if file_format == "png":

            img.save(img_io, "PNG")

            img_io.seek(0)

            return send_file(

                img_io,

                mimetype="image/png",

                as_attachment=True,

                download_name="qr.png"
            )

        # =====================================
        # PDF
        # =====================================

        elif file_format == "pdf":

            pdf_io = io.BytesIO()

            temp_path = "temp_qr.png"

            img.save(temp_path)

            c = canvas.Canvas(
                pdf_io,
                pagesize=letter
            )

            c.drawImage(

                temp_path,

                150,

                400,

                width=250,

                height=250
            )

            c.save()

            os.remove(temp_path)

            pdf_io.seek(0)

            return send_file(

                pdf_io,

                mimetype="application/pdf",

                as_attachment=True,

                download_name="qr.pdf"
            )

        # =====================================
        # JPEG
        # =====================================

        else:

            img.save(img_io, "JPEG")

            img_io.seek(0)

            return send_file(

                img_io,

                mimetype="image/jpeg",

                as_attachment=True,

                download_name="qr.jpeg"
            )

    except Exception as e:

        print("DOWNLOAD ERROR =", e)

        return jsonify({
            "error": str(e)
        })

# =========================================
# RUN
# =========================================

if __name__ == "__main__":

    with app.app_context():

        db.create_all()

    app.run(

        host="0.0.0.0",

        port=10000,

        debug=True
    )