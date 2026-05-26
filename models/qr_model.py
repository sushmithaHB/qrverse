from flask_sqlalchemy import SQLAlchemy

from datetime import datetime

import random
import string

db = SQLAlchemy()


# ==========================
# SHORT ID GENERATOR
# ==========================

def generate_short_id():

    return ''.join(

        random.choices(

            string.ascii_letters +
            string.digits,

            k=6

        )

    )


# ==========================
# QR MODEL
# ==========================

class QRCode(db.Model):

    id = db.Column(

        db.Integer,

        primary_key=True
    )

    short_id = db.Column(

        db.String(10),

        unique=True,

        nullable=False,

        default=generate_short_id
    )

    original_data = db.Column(

        db.Text,

        nullable=False
    )

    qr_type = db.Column(

        db.String(100),

        nullable=False
    )

    scans = db.Column(

        db.Integer,

        default=0
    )

    last_scanned = db.Column(

        db.DateTime,

        nullable=True
    )

    created_at = db.Column(

        db.DateTime,

        default=datetime.utcnow
    )