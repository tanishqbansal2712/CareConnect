
class Config:
    # ── Database ───────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI     = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── JWT ────────────────────────────────────────────────────
    JWT_SECRET_KEY = "super-secret-key"

    # ── Redis / Celery ─────────────────────────────────────────
    REDIS_URL             = "redis://localhost:6379/0"
    broken_url    = "redis://localhost:6379/0"
    result_backend = "redis://localhost:6379/0"

    # ── Flask-Caching (Redis) ──────────────────────────────────
    CACHE_TYPE            = "RedisCache"
    CACHE_REDIS_URL       = "redis://localhost:6379/0"
    CACHE_DEFAULT_TIMEOUT = 300          # 5 minutes default

    # ── Flask-Mail (Gmail SMTP) ────────────────────────────────
    # Set these in a real .env file — never hardcode in production
    MAIL_SERVER   = "smtp.gmail.com"
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = "mail@gmail.com"
    MAIL_PASSWORD = "xxxx xxxx xxxx xxxx"
    MAIL_DEFAULT_SENDER = ("CareConnect Hospital", "mailgmail.com")