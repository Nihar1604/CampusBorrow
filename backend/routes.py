from datetime import datetime, timezone
from functools import wraps
from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from models import db, User, Resource, BorrowRequest

bcrypt = Bcrypt()
jwt = JWTManager()
api_bp = Blueprint('api', __name__)


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = db.session.get(User, int(user_id)) if user_id else None
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


def parse_datetime(dt_str):
    if not dt_str:
        return None
    cleaned = dt_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        dt = datetime.strptime(cleaned, "%Y-%m-%d")

    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


# ---------------------------------------------------------
# Authentication Endpoints
# ---------------------------------------------------------
@api_bp.route('/api/auth/register', methods=['POST'])
@api_bp.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    roll_no = data.get('roll_no', '').strip() or None
    department = data.get('department', 'AIDS').strip() or "AIDS"
    is_admin = bool(data.get('is_admin', False))

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
    user = User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        is_admin=is_admin,
        roll_no=roll_no,
        department=department
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@api_bp.route('/api/auth/login', methods=['POST'])
@api_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = (data.get('username') or data.get('email') or '').strip()
    password = data.get('password', '')

    if not identifier or not password:
        return jsonify({'error': 'Username/email and password are required'}), 400

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    )

    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@api_bp.route('/api/auth/me', methods=['GET'])
@api_bp.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id else None
    if not user:
        return jsonify({'error': 'User not found'}), 404

    active_borrows = [b.to_dict() for b in user.borrows if b.effective_status in ['pending', 'approved', 'overdue']]
    return jsonify({
        'user': user.to_dict(),
        'active_borrows': active_borrows,
        'active_count': len(active_borrows)
    }), 200


# ---------------------------------------------------------
# Resource Management Endpoints
# ---------------------------------------------------------
@api_bp.route('/api/resources', methods=['GET'])
def list_resources():
    category = request.args.get('category', '').strip()
    search = request.args.get('search', '').strip()

    query = Resource.query

    if category and category.lower() != 'all':
        query = query.filter(Resource.category.ilike(f"%{category}%"))

    if search:
        query = query.filter(
            (Resource.name.ilike(f"%{search}%")) |
            (Resource.description.ilike(f"%{search}%")) |
            (Resource.location.ilike(f"%{search}%"))
        )

    resources = query.order_by(Resource.id.asc()).all()
    return jsonify({
        'resources': [r.to_dict() for r in resources],
        'count': len(resources)
    }), 200


@api_bp.route('/api/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    return jsonify({'resource': resource.to_dict()}), 200


@api_bp.route('/api/resources', methods=['POST'])
@admin_required
def create_resource():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Resource name is required'}), 400

    try:
        total_quantity = int(data.get('total_quantity', 1))
        available_quantity = int(data.get('available_quantity', total_quantity))
    except (ValueError, TypeError):
        return jsonify({'error': 'Quantities must be valid integers'}), 400

    if total_quantity < 1:
        return jsonify({'error': 'Total quantity must be at least 1'}), 400

    if available_quantity < 0 or available_quantity > total_quantity:
        return jsonify({'error': 'Available quantity must be between 0 and total quantity'}), 400

    resource = Resource(
        name=name,
        category=data.get('category', 'Lab Equipment').strip(),
        description=data.get('description', '').strip(),
        location=data.get('location', 'AI & DS Lab 304').strip(),
        total_quantity=total_quantity,
        available_quantity=available_quantity,
        status=data.get('status', 'available').strip()
    )
    db.session.add(resource)
    db.session.commit()

    return jsonify({
        'message': 'Resource created successfully',
        'resource': resource.to_dict()
    }), 201


def _update_resource_quantities(resource, data):
    if 'total_quantity' in data:
        try:
            tq = int(data['total_quantity'])
            if tq < 0:
                return 'Total quantity cannot be negative'
            resource.total_quantity = tq
        except (ValueError, TypeError):
            return 'Invalid total quantity'

    if 'available_quantity' in data:
        try:
            aq = int(data['available_quantity'])
            if aq < 0:
                return 'Available quantity cannot be negative'
            if aq > resource.total_quantity:
                return 'Available quantity cannot exceed total quantity'
            resource.available_quantity = aq
        except (ValueError, TypeError):
            return 'Invalid available quantity'
    return None


@api_bp.route('/api/resources/<int:resource_id>', methods=['PUT'])
@admin_required
def update_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404

    data = request.get_json() or {}
    if 'name' in data:
        name = str(data['name']).strip()
        if not name:
            return jsonify({'error': 'Resource name cannot be empty'}), 400
        resource.name = name

    for field in ['category', 'description', 'location']:
        if field in data:
            setattr(resource, field, str(data[field]).strip())

    if 'status' in data and data['status'] in ['available', 'unavailable', 'maintenance']:
        resource.status = str(data['status']).strip()

    err = _update_resource_quantities(resource, data)
    if err:
        return jsonify({'error': err}), 400

    db.session.commit()
    return jsonify({
        'message': 'Resource updated successfully',
        'resource': resource.to_dict()
    }), 200


@api_bp.route('/api/resources/<int:resource_id>', methods=['DELETE'])
@admin_required
def delete_resource(resource_id):
    resource = db.session.get(Resource, resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404

    active_borrows = BorrowRequest.query.filter(
        BorrowRequest.resource_id == resource_id,
        BorrowRequest.status.in_(['approved', 'overdue'])
    ).first()

    if active_borrows:
        return jsonify({'error': 'Cannot delete resource with active approved borrowings'}), 409

    BorrowRequest.query.filter_by(resource_id=resource_id).delete()
    db.session.delete(resource)
    db.session.commit()

    return jsonify({'message': 'Resource deleted successfully'}), 200


# ---------------------------------------------------------
# Borrowing & Lending Workflow Endpoints
# ---------------------------------------------------------
def _validate_borrow_inputs(data, resource):
    try:
        qty = int(data.get('quantity', 1))
        if qty < 1:
            return None, None, ('Quantity must be at least 1', 400)
    except (ValueError, TypeError):
        return None, None, ('Quantity must be a valid integer', 400)

    if resource.status != 'available':
        return None, None, (f'Resource is currently {resource.status}', 409)

    if resource.available_quantity < qty:
        return None, None, ('Requested quantity exceeds available stock', 409)

    try:
        due_date = parse_datetime(data.get('due_date'))
    except Exception:
        return None, None, ('Invalid due_date format', 400)

    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    if not due_date or due_date <= now_naive:
        return None, None, ('Due date must be in the future', 400)

    return qty, due_date, None


@api_bp.route('/api/borrows', methods=['POST'])
@jwt_required()
def request_borrow():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id else None
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    resource_id = data.get('resource_id')
    if not resource_id or not data.get('due_date'):
        return jsonify({'error': 'resource_id and due_date are required'}), 400

    resource = db.session.get(Resource, resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404

    qty, due_date, err = _validate_borrow_inputs(data, resource)
    if err:
        return jsonify({'error': err[0]}), err[1]

    borrow = BorrowRequest(
        user_id=user.id,
        resource_id=resource.id,
        quantity=qty,
        purpose=data.get('purpose', '').strip(),
        due_date=due_date,
        status='pending'
    )
    db.session.add(borrow)
    db.session.commit()

    return jsonify({
        'message': 'Borrow request submitted successfully',
        'borrow': borrow.to_dict()
    }), 201


@api_bp.route('/api/borrows/my', methods=['GET'])
@jwt_required()
def my_borrows():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id else None
    if not user:
        return jsonify({'error': 'User not found'}), 404

    borrows = BorrowRequest.query.filter_by(user_id=user.id).order_by(BorrowRequest.borrow_date.desc()).all()
    return jsonify({
        'borrows': [b.to_dict() for b in borrows],
        'count': len(borrows)
    }), 200


@api_bp.route('/api/borrows', methods=['GET'])
@admin_required
def list_all_borrows():
    all_borrows = BorrowRequest.query.order_by(BorrowRequest.borrow_date.desc()).all()

    total_resources = Resource.query.count()
    total_stock = db.session.query(db.func.sum(Resource.total_quantity)).scalar() or 0
    available_stock = db.session.query(db.func.sum(Resource.available_quantity)).scalar() or 0
    pending_count = BorrowRequest.query.filter_by(status='pending').count()
    active_count = sum(1 for b in all_borrows if b.effective_status == 'approved')
    overdue_count = sum(1 for b in all_borrows if b.effective_status == 'overdue')

    return jsonify({
        'borrows': [b.to_dict() for b in all_borrows],
        'stats': {
            'total_resources': total_resources,
            'total_stock': total_stock,
            'available_stock': available_stock,
            'pending_approvals': pending_count,
            'active_borrows': active_count,
            'overdue_items': overdue_count
        }
    }), 200


@api_bp.route('/api/borrows/<int:borrow_id>/approve', methods=['PUT'])
@admin_required
def approve_borrow(borrow_id):
    borrow = db.session.get(BorrowRequest, borrow_id)
    if not borrow:
        return jsonify({'error': 'Borrow request not found'}), 404

    if borrow.status != 'pending':
        return jsonify({'error': f"Cannot approve request with status '{borrow.status}'"}), 400

    resource = borrow.resource
    if resource.available_quantity < borrow.quantity:
        return jsonify({'error': 'Insufficient available quantity to approve this request'}), 409

    resource.available_quantity -= borrow.quantity
    if resource.available_quantity == 0:
        resource.status = 'unavailable'

    borrow.status = 'approved'
    db.session.commit()

    return jsonify({
        'message': 'Borrow request approved successfully',
        'borrow': borrow.to_dict()
    }), 200


@api_bp.route('/api/borrows/<int:borrow_id>/reject', methods=['PUT'])
@admin_required
def reject_borrow(borrow_id):
    borrow = db.session.get(BorrowRequest, borrow_id)
    if not borrow:
        return jsonify({'error': 'Borrow request not found'}), 404

    if borrow.status != 'pending':
        return jsonify({'error': f"Cannot reject request with status '{borrow.status}'"}), 400

    data = request.get_json() or {}
    admin_remarks = data.get('admin_remarks', '').strip()

    borrow.status = 'rejected'
    if admin_remarks:
        borrow.admin_remarks = admin_remarks

    db.session.commit()
    return jsonify({
        'message': 'Borrow request rejected',
        'borrow': borrow.to_dict()
    }), 200


@api_bp.route('/api/borrows/<int:borrow_id>/return', methods=['PUT'])
@jwt_required()
def return_borrow(borrow_id):
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id)) if user_id else None
    if not user:
        return jsonify({'error': 'User not found'}), 404

    borrow = db.session.get(BorrowRequest, borrow_id)
    if not borrow:
        return jsonify({'error': 'Borrow request not found'}), 404

    if not user.is_admin and borrow.user_id != user.id:
        return jsonify({'error': 'Unauthorized to return this item'}), 403

    if borrow.status == 'returned':
        return jsonify({'error': 'Item has already been returned'}), 400

    if borrow.status not in ['approved', 'overdue']:
        return jsonify({'error': f"Cannot return an unapproved request (status: {borrow.status})"}), 400

    resource = borrow.resource
    resource.available_quantity += borrow.quantity
    if resource.status == 'unavailable' and resource.available_quantity > 0:
        resource.status = 'available'

    borrow.status = 'returned'
    borrow.return_date = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()

    return jsonify({
        'message': 'Item returned successfully',
        'borrow': borrow.to_dict()
    }), 200


def init_routes(app):
    bcrypt.init_app(app)
    jwt.init_app(app)
    app.register_blueprint(api_bp)
