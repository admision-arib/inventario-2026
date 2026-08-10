import os
from .base import *

DEBUG = False

# Hosts permitidos (lee del .env)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', default='127.0.0.1,localhost').split(',')

# Seguridad HTTP / Cabeceras
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# SSL / Cookies (desactivado porque el proxy de Virtualmin ya maneja HTTPS)
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Indicar a Django que el proxy maneja SSL/HTTPS (necesario para que las URLs generadas sean https)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Manejo de Estáticos y Media en Producción
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Orígenes confiables para CSRF (lee del .env)
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', default='https://inventario.iestparib.edu.pe,http://inventario.iestparib.edu.pe').split(',')