from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utc_now():
    """Return timezone-naive UTC timestamp for standard DB storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    roll_no = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(50), default="AIDS", nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    borrows = db.relationship('BorrowRequest', back_populates='user', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'role': 'Admin / Lab Coordinator' if self.is_admin else 'Student',
            'roll_no': self.roll_no,
            'department': self.department,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Resource(db.Model):
    __tablename__ = 'resource'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False, default="Lab Equipment")
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=False, default="AI & DS Lab 304")
    total_quantity = db.Column(db.Integer, default=1, nullable=False)
    available_quantity = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(30), default="available", nullable=False)  # "available", "unavailable", "maintenance"
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    borrows = db.relationship('BorrowRequest', back_populates='resource', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'location': self.location,
            'total_quantity': self.total_quantity,
            'available_quantity': self.available_quantity,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BorrowRequest(db.Model):
    __tablename__ = 'borrow_request'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    purpose = db.Column(db.String(255), nullable=True)
    borrow_date = db.Column(db.DateTime, default=utc_now, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(30), default="pending", nullable=False)  # "pending", "approved", "rejected", "returned", "overdue"
    admin_remarks = db.Column(db.String(255), nullable=True)

    # Relationships
    user = db.relationship('User', back_populates='borrows')
    resource = db.relationship('Resource', back_populates='borrows')

    @property
    def effective_status(self):
        # Dynamically flag as overdue if status is approved and due_date is in the past
        if self.status == 'approved' and self.due_date:
            due = self.due_date
            if due.tzinfo is not None:
                due = due.astimezone(timezone.utc).replace(tzinfo=None)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if due < now:
                return 'overdue'
        return self.status

    def to_dict(self):
        current_status = self.effective_status
        return {
            'id': self.id,
            'user_id': self.user_id,
            'resource_id': self.resource_id,
            'quantity': self.quantity,
            'purpose': self.purpose,
            'borrow_date': self.borrow_date.isoformat() if self.borrow_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'status': current_status,
            'raw_status': self.status,
            'admin_remarks': self.admin_remarks,
            'user': {
                'id': self.user.id if self.user else None,
                'username': self.user.username if self.user else None,
                'email': self.user.email if self.user else None,
                'roll_no': self.user.roll_no if self.user else None,
                'department': self.user.department if self.user else None,
            } if self.user else None,
            'resource': {
                'id': self.resource.id if self.resource else None,
                'name': self.resource.name if self.resource else None,
                'category': self.resource.category if self.resource else None,
                'location': self.resource.location if self.resource else None,
                'available_quantity': self.resource.available_quantity if self.resource else 0,
            } if self.resource else None,
        }


def seed_database(app, bcrypt):
    """Seed initial admin, student, and campus resources if database is empty."""
    with app.app_context():
        # Check if users exist
        if db.session.query(User).first() is None:
            admin_user = User(
                username="admin",
                email="admin@vit.edu",
                password_hash=bcrypt.generate_password_hash("Admin@123").decode('utf-8'),
                is_admin=True,
                roll_no="FAC-001",
                department="AIDS"
            )
            student_user = User(
                username="student",
                email="student@vit.edu",
                password_hash=bcrypt.generate_password_hash("Student@123").decode('utf-8'),
                is_admin=False,
                roll_no="12110543",
                department="AIDS"
            )
            db.session.add_all([admin_user, student_user])
            db.session.commit()
            print(" Default users seeded (admin@vit.edu / student@vit.edu).")

        # Check if resources exist
        if db.session.query(Resource).first() is None:
            sample_resources = [
                Resource(
                    name="ESP32-S3 DevKit",
                    category="Electronics",
                    description="Dual-core Xtensa LX7 MCU with Wi-Fi & BLE 5.0 for IoT and embedded ML projects",
                    location="AI & DS Lab 304",
                    total_quantity=10,
                    available_quantity=10,
                    status="available"
                ),
                Resource(
                    name="DSLR Camera Kit",
                    category="Club Gear",
                    description="Canon EOS 1500D with 18-55mm lens and tripod for campus media & club coverage",
                    location="Central Innovation Hub",
                    total_quantity=3,
                    available_quantity=3,
                    status="available"
                ),
                Resource(
                    name="Oscilloscope Probe Set",
                    category="Lab Equipment",
                    description="100MHz 10:1 passive oscilloscope probe with ground lead and IC test clips",
                    location="Instrumentation Lab 202",
                    total_quantity=8,
                    available_quantity=8,
                    status="available"
                ),
                Resource(
                    name="Arduino Sensor Kit",
                    category="Electronics",
                    description="37-in-1 modular sensor kit including ultrasonic, IR, gas, flame, and DHT11 sensors",
                    location="AI & DS Lab 304",
                    total_quantity=15,
                    available_quantity=15,
                    status="available"
                ),
                Resource(
                    name="Raspberry Pi 4 Model B (8GB)",
                    category="Electronics",
                    description="Quad-core Cortex-A72 with 8GB RAM for edge computing, robotics & computer vision",
                    location="Robotics & Automation Lab",
                    total_quantity=6,
                    available_quantity=6,
                    status="available"
                ),
                Resource(
                    name="NVIDIA Jetson Nano Dev Kit",
                    category="Lab Equipment",
                    description="128-core Maxwell GPU board for real-time edge AI inference and deep learning pipelines",
                    location="AI & DS Lab 304",
                    total_quantity=4,
                    available_quantity=4,
                    status="available"
                )
            ]
            db.session.add_all(sample_resources)
            db.session.commit()
            print(" 6 initial campus resources seeded.")
