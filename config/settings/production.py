import os
from .base import *

DEBUG = False

# Hosts permitidos
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')

# Seguridad HTTP / Cabeceras
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Manejo de SSL / HTTPS (si no usas certificado SSL en el servidor, déjalos en False en el .env)
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'

# Manejo de Estáticos y Media en Producción
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Orígenes confiables para evitar bloqueos por CSRF en peticiones POST (importación Excel, etc.)
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', default='http://127.0.0.1').split(',')