from pathlib import Path
from .base import *

DEBUG = False

# ========== PROXY INVERSO ==========
# IMPORTANTE: En nginx debe existir: proxy_set_header X-Forwarded-Proto $scheme;
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = False

# ========== HTTPS OBLIGATORIO ========== [FIX REG-01 + SEC-11]
SECURE_SSL_REDIRECT = False  # <--- REPONER ESTA LÍNEA, es la regresión crítica
SECURE_PROXY_SSL_HEADER = None  # <--- None, porque no te está mandando el header

SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ========== COOKIES SEGURAS ==========
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_AGE = 3600  # 1 hora, expira
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# ========== HEADERS SEGURIDAD ==========
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
# SEC-10/11 - Preparación para CSP futura
# SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# ========== CSRF ==========
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://inventario.iestparib.edu.pe'
).split(',')

# ========== LOGGING ========== [FIX SEC-18]
# FIX: No hacer mkdir() en tiempo de import si no hay permisos, rompe el arranque
LOGS_DIR = Path('/home/iestparib/logs')
try:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Fallback para CI o si el usuario no tiene permisos
    LOGS_DIR = Path(BASE_DIR / 'logs')
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'rotating_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django_error.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django_security.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['rotating_file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['rotating_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps': {
            'handlers': ['rotating_file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# ========== CHECKS DE PRODUCCIÓN ==========
# Esto hará que `check --deploy` falle si falta algo
SILENCED_SYSTEM_CHECKS = []