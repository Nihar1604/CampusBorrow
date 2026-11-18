import os
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_talisman import Talisman
from prometheus_flask_exporter import PrometheusMetrics
from dotenv import load_dotenv

from models import db, seed_database
from routes import init_routes, bcrypt

load_dotenv()


def _resolve_frontend_dir():
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    if not os.path.isdir(frontend_dir):
        frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend'))
    return frontend_dir


def _get_database_uri():
    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql://", 1)
    return db_url or "sqlite:////tmp/campusborrow.db"  # nosec B108


def _configure_security(app):
    csp = {
        'default-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https:", "data:"],
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        'font-src': ["'self'", "https://fonts.gstatic.com", "data:"],
        'img-src': ["'self'", "data:", "https:"]
    }
    force_https = str(os.getenv("FORCE_HTTPS", "False")).lower() in ("true", "1")
    Talisman(
        app,
        force_https=force_https,
        content_security_policy=csp,
        frame_options='SAMEORIGIN'
    )


def _configure_metrics(app):
    if app.config.get('TESTING'):
        from prometheus_client import CollectorRegistry
        metric_registry = CollectorRegistry(auto_describe=True)
    else:
        from prometheus_client import REGISTRY
        metric_registry = REGISTRY

    metrics = PrometheusMetrics(app, registry=metric_registry, group_by='endpoint')
    try:
        metrics.info('campusborrow_info', 'CampusBorrow Portal info', version='1.0.0')
    except Exception:
        pass
    return metrics


def _register_static_routes(app, frontend_dir):
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "campusborrow-backend"
        }), 200

    @app.route('/')
    def index():
        if os.path.exists(os.path.join(frontend_dir, 'index.html')):
            return send_from_directory(frontend_dir, 'index.html')
        return jsonify({"service": "campusborrow-backend", "status": "running"}), 200

    @app.route('/<path:path>')
    def serve_frontend_assets(path):
        if not path.startswith('api/') and not path.startswith('metrics'):
            target_path = os.path.join(frontend_dir, path)
            if os.path.exists(target_path):
                return send_from_directory(frontend_dir, path)
            index_path = os.path.join(frontend_dir, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(frontend_dir, 'index.html')
        return jsonify({"error": "Not found"}), 404


def create_app(test_config=None):
    instance_dir = os.path.abspath("/tmp/instance")  # nosec B108
    os.makedirs(instance_dir, exist_ok=True)
    frontend_dir = _resolve_frontend_dir()
    app = Flask(
        __name__,
        instance_path=instance_dir,
        static_folder=frontend_dir
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = _get_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv("SECRET_KEY", "campusborrow-dev-secret-key-vit-2026")
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

    if test_config:
        app.config.update(test_config)

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    _configure_security(app)
    _configure_metrics(app)

    db.init_app(app)
    init_routes(app)
    _register_static_routes(app, frontend_dir)

    if not app.config.get('TESTING'):
        with app.app_context():
            db.create_all()
            seed_database(app, bcrypt)

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database(app, bcrypt)
        print(" CampusBorrow tables created & verified.")
        print(" Using DB:", app.config["SQLALCHEMY_DATABASE_URI"])
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1")
    host_addr = os.getenv("FLASK_HOST", "0.0.0.0")  # nosec B104
    port_num = int(os.getenv("PORT", os.getenv("FLASK_PORT", "8080")))
    app.run(debug=debug_mode, host=host_addr, port=port_num)
