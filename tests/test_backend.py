import os
import sys
from datetime import datetime, timedelta, timezone
import pytest

# Ensure backend directory is in the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app import create_app
from models import db, User, Resource, BorrowRequest, seed_database
from routes import bcrypt


@pytest.fixture
def app():
    """Create test application configured with an in-memory SQLite database."""
    test_app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key-vit-devops-2026-campusborrow-enterprise-length-secret",
    })

    with test_app.app_context():
        db.create_all()
        seed_database(test_app, bcrypt)
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client fixture."""
    return app.test_client()


def get_token(client, identifier, password):
    """Helper to authenticate and return JWT access token."""
    res = client.post("/api/auth/login", json={
        "username": identifier,
        "password": password
    })
    assert res.status_code == 200, f"Login failed for {identifier}: {res.get_json()}"
    return res.get_json()["access_token"]


@pytest.fixture
def admin_headers(client):
    token = get_token(client, "admin@vit.edu", "Admin@123")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student_headers(client):
    token = get_token(client, "student@vit.edu", "Student@123")
    return {"Authorization": f"Bearer {token}"}


# ===================================================================
# 1. DevSecOps, Health & Observability Endpoints
# ===================================================================
def test_health_check(client):
    """Verify health check endpoint returns 200 with service identification."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "campusborrow-backend"


def test_metrics_endpoint(client):
    """Verify Prometheus metrics endpoint exposes metrics for monitoring."""
    res = client.get("/metrics")
    assert res.status_code == 200
    metrics_text = res.data.decode("utf-8")
    assert "flask_http_request_total" in metrics_text or "campusborrow" in metrics_text


def test_security_headers(client):
    """Verify DevSecOps security headers injected by Flask-Talisman."""
    res = client.get("/api/health")
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert "X-Frame-Options" in headers
    assert "Content-Security-Policy" in headers


# ===================================================================
# 2. Database Seeding & Authentication
# ===================================================================
def test_seed_data_initialization(app):
    """Verify default admin, student, and campus resources are seeded."""
    with app.app_context():
        admin = User.query.filter_by(email="admin@vit.edu").first()
        student = User.query.filter_by(email="student@vit.edu").first()
        assert admin is not None
        assert admin.is_admin is True
        assert student is not None
        assert student.is_admin is False

        resources = Resource.query.all()
        assert len(resources) >= 6
        resource_names = [r.name for r in resources]
        assert "ESP32-S3 DevKit" in resource_names
        assert "DSLR Camera Kit" in resource_names
        assert "Arduino Sensor Kit" in resource_names


def test_user_registration(client):
    """Test new student registration and duplicate checking."""
    reg_data = {
        "username": "rohan_vit",
        "email": "rohan.sharma@vit.edu",
        "password": "Password@123",
        "roll_no": "12110888",
        "department": "AIDS"
    }
    res = client.post("/api/auth/register", json=reg_data)
    assert res.status_code == 201
    data = res.get_json()
    assert data["user"]["username"] == "rohan_vit"
    assert data["user"]["email"] == "rohan.sharma@vit.edu"
    assert data["user"]["is_admin"] is False

    # Duplicate username check
    res_dup_user = client.post("/api/auth/register", json=reg_data)
    assert res_dup_user.status_code == 409

    # Duplicate email check
    reg_data2 = reg_data.copy()
    reg_data2["username"] = "different_user"
    res_dup_email = client.post("/api/auth/register", json=reg_data2)
    assert res_dup_email.status_code == 409


def test_user_login_success_and_failure(client):
    """Test authentication success with username or email, and failure with invalid credentials."""
    # Login with email
    res1 = client.post("/api/auth/login", json={
        "username": "student@vit.edu",
        "password": "Student@123"
    })
    assert res1.status_code == 200
    assert "access_token" in res1.get_json()

    # Login with username
    res2 = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "Admin@123"
    })
    assert res2.status_code == 200
    assert res2.get_json()["user"]["is_admin"] is True

    # Bad password
    res_bad = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "WrongPassword"
    })
    assert res_bad.status_code == 401


def test_get_current_user_profile(client, student_headers):
    """Test /api/auth/me profile retrieval."""
    res = client.get("/api/auth/me", headers=student_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["user"]["email"] == "student@vit.edu"
    assert "active_borrows" in data


# ===================================================================
# 3. Resource Management (Catalog & Admin CRUD)
# ===================================================================
def test_resource_listing_and_filtering(client):
    """Test listing all resources and filtering by category and search."""
    # List all
    res = client.get("/api/resources")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] >= 6

    # Filter by category
    res_cat = client.get("/api/resources?category=Electronics")
    assert res_cat.status_code == 200
    cat_resources = res_cat.get_json()["resources"]
    assert all("Electronics" in r["category"] for r in cat_resources)

    # Search keyword
    res_search = client.get("/api/resources?search=ESP32")
    assert res_search.status_code == 200
    search_resources = res_search.get_json()["resources"]
    assert len(search_resources) >= 1
    assert "ESP32" in search_resources[0]["name"]


def test_admin_create_resource(client, admin_headers, student_headers):
    """Test that only admin can create resources."""
    new_res_data = {
        "name": "FPGA Xilinx Spartan-7 Board",
        "category": "Electronics",
        "description": "Spartan-7 XC7S25 development board for digital logic & embedded systems",
        "location": "VLSI Lab 101",
        "total_quantity": 5,
        "available_quantity": 5,
        "status": "available"
    }

    # Student should be forbidden (403)
    res_unauth = client.post("/api/resources", json=new_res_data, headers=student_headers)
    assert res_unauth.status_code == 403

    # Admin should succeed (201)
    res_auth = client.post("/api/resources", json=new_res_data, headers=admin_headers)
    assert res_auth.status_code == 201
    created = res_auth.get_json()["resource"]
    assert created["name"] == "FPGA Xilinx Spartan-7 Board"
    assert created["total_quantity"] == 5


def test_admin_update_resource(client, admin_headers, student_headers):
    """Test admin updating resource details and status."""
    # Update resource ID 1
    res = client.put("/api/resources/1", json={
        "status": "maintenance",
        "available_quantity": 2
    }, headers=admin_headers)
    assert res.status_code == 200
    updated = res.get_json()["resource"]
    assert updated["status"] == "maintenance"
    assert updated["available_quantity"] == 2

    # Non-admin forbidden
    res_forbidden = client.put("/api/resources/1", json={"status": "available"}, headers=student_headers)
    assert res_forbidden.status_code == 403


# ===================================================================
# 4. Borrowing Workflow, Validations & Stock Decrement/Restoration
# ===================================================================
def test_student_borrow_request_lifecycle(client, student_headers, admin_headers):
    """Test full cycle: student request -> admin approve -> student return."""
    # Get initial resource
    res_initial = client.get("/api/resources/1").get_json()["resource"]
    init_avail = res_initial["available_quantity"]
    assert init_avail > 0

    future_due = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()

    # Step 1: Student creates borrow request
    borrow_payload = {
        "resource_id": 1,
        "quantity": 2,
        "due_date": future_due,
        "purpose": "PEC2 Edge AI Prototype"
    }
    res_req = client.post("/api/borrows", json=borrow_payload, headers=student_headers)
    assert res_req.status_code == 201
    borrow = res_req.get_json()["borrow"]
    borrow_id = borrow["id"]
    assert borrow["status"] == "pending"
    assert borrow["quantity"] == 2

    # Stock should NOT decrement while pending
    res_check1 = client.get("/api/resources/1").get_json()["resource"]
    assert res_check1["available_quantity"] == init_avail

    # Step 2: Admin approves request -> atomically decrements available_quantity
    res_appr = client.put(f"/api/borrows/{borrow_id}/approve", headers=admin_headers)
    assert res_appr.status_code == 200
    assert res_appr.get_json()["borrow"]["status"] == "approved"

    res_check2 = client.get("/api/resources/1").get_json()["resource"]
    assert res_check2["available_quantity"] == init_avail - 2

    # Step 3: Item return -> atomically restores available_quantity
    res_ret = client.put(f"/api/borrows/{borrow_id}/return", headers=student_headers)
    assert res_ret.status_code == 200
    assert res_ret.get_json()["borrow"]["status"] == "returned"

    res_check3 = client.get("/api/resources/1").get_json()["resource"]
    assert res_check3["available_quantity"] == init_avail


def test_borrow_validation_future_due_date(client, student_headers):
    """Test that requesting with a past due date is rejected with 400 Bad Request."""
    past_due = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    res = client.post("/api/borrows", json={
        "resource_id": 1,
        "quantity": 1,
        "due_date": past_due,
        "purpose": "Invalid past test"
    }, headers=student_headers)
    assert res.status_code == 400
    assert "Due date must be in the future" in res.get_json()["error"]


def test_borrow_out_of_stock_conflict(client, student_headers):
    """Test that requesting quantity exceeding available stock returns 409 Conflict."""
    future_due = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    res = client.post("/api/borrows", json={
        "resource_id": 1,
        "quantity": 999,  # Far exceeds stock
        "due_date": future_due,
        "purpose": "Overstock test"
    }, headers=student_headers)
    assert res.status_code == 409
    assert "exceeds available stock" in res.get_json()["error"]


def test_admin_reject_request(client, student_headers, admin_headers):
    """Test admin rejecting a pending borrow request with optional remarks."""
    future_due = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    res_req = client.post("/api/borrows", json={
        "resource_id": 2,
        "quantity": 1,
        "due_date": future_due,
        "purpose": "Club photography"
    }, headers=student_headers)
    borrow_id = res_req.get_json()["borrow"]["id"]

    res_rej = client.put(f"/api/borrows/{borrow_id}/reject", json={
        "admin_remarks": "Camera reserved for College Annual Day"
    }, headers=admin_headers)
    assert res_rej.status_code == 200
    data = res_rej.get_json()["borrow"]
    assert data["status"] == "rejected"
    assert data["admin_remarks"] == "Camera reserved for College Annual Day"


def test_dynamic_overdue_detection(client, app, student_headers, admin_headers):
    """Test that an approved borrowing past its due date dynamically reflects 'overdue'."""
    with app.app_context():
        user = User.query.filter_by(email="student@vit.edu").first()
        res = Resource.query.first()
        past_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)

        overdue_req = BorrowRequest(
            user_id=user.id,
            resource_id=res.id,
            quantity=1,
            purpose="Overdue demonstration",
            due_date=past_time,
            status="approved"
        )
        db.session.add(overdue_req)
        db.session.commit()
        borrow_id = overdue_req.id

    # Check student's borrowing history
    res_my = client.get("/api/borrows/my", headers=student_headers)
    assert res_my.status_code == 200
    my_borrows = res_my.get_json()["borrows"]
    overdue_item = next(b for b in my_borrows if b["id"] == borrow_id)
    assert overdue_item["status"] == "overdue"

    # Check admin summary stats
    res_admin = client.get("/api/borrows", headers=admin_headers)
    assert res_admin.status_code == 200
    stats = res_admin.get_json()["stats"]
    assert stats["overdue_items"] >= 1


def test_delete_resource_blocked_with_active_borrow(client, app, admin_headers):
    """Test that deleting a resource with active approved borrowings is blocked with 409 Conflict."""
    with app.app_context():
        user = User.query.filter_by(email="student@vit.edu").first()
        res_item = Resource.query.first()
        res_id = res_item.id

        active_borrow = BorrowRequest(
            user_id=user.id,
            resource_id=res_id,
            quantity=1,
            purpose="Active loan blocking delete",
            due_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2),
            status="approved"
        )
        db.session.add(active_borrow)
        db.session.commit()

    # Attempt delete while active approved borrow exists -> 409
    res_del = client.delete(f"/api/resources/{res_id}", headers=admin_headers)
    assert res_del.status_code == 409
    assert "Cannot delete resource with active approved borrowings" in res_del.get_json()["error"]
