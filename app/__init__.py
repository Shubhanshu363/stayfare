from flask import Flask

from config import Config
from .extensions import db, login_manager, migrate


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

        from .seed import seed_demo_data
        seed_demo_data()

    return app
