import os

# Lee la variable de entorno o carga local por defecto
environment = os.getenv('DJANGO_ENV', 'local')

if environment == 'production':
    from .production import *
else:
    from .local import *