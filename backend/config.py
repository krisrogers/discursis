"""Class-based application configuration."""


class ConfigClass(object):
    """Flask application config."""

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'
    SECURITY_PASSWORD_SALT = 'ttoZo2MkBP'
    TRAP_BAD_REQUEST_ERRORS = True
    SECURITY_REGISTERABLE = True
    SECURITY_REGISTER_URL = '/register/'
    SECURITY_SEND_REGISTER_EMAIL = True

    WTF_CSRF_ENABLED = False
    CORS_HEADERS = 'Content-Type'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024    # 5 Mb limit
    CELERY_BROKER_URL = 'redis://localhost:6379',
    CELERY_RESULT_BACKEND = 'redis://localhost:6379'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///storage.db'    # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings
    MAIL_SERVER = 'smtp.mailgun.org'
    MAIL_PORT = 587
    # MAIL_USE_SSL = True
    MAIL_USE_TLS = True

    # Flask-Mail SMTP account settings
    MAIL_USERNAME = 'postmaster@sandbox0d4f986865614c7e83020c33368e2f8e.mailgun.org'
    MAIL_PASSWORD = '34117e92926f9e2dff0525900160fc28-bdd08c82-f957748e'
