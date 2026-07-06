from flask import Flask

from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig
from .extensions import db, login_manager, migrate


def create_app(config_object=None):
    app = Flask(__name__)

    if config_object is None:
        env = app.config.get("ENV", "development")
        if env == "testing":
            config_object = TestingConfig
        elif env == "production":
            config_object = ProductionConfig
        else:
            config_object = DevelopmentConfig

    app.config.from_object(config_object)

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
