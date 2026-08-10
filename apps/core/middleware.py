import threading

_thread_locals = threading.local()


def get_current_user():
    """Retorna el usuario actual almacenado en el hilo de ejecución."""
    return getattr(_thread_locals, 'user', None)


class ThreadLocalUserMiddleware:
    """
    Middleware que inyecta el usuario autenticado en el hilo de ejecución actual.
    Satisface el Driver QA-1 (Auditoría Transversal).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Almacenar el usuario si está autenticado
        _thread_locals.user = request.user if request.user.is_authenticated else None

        try:
            # 2. Procesar la petición HTTP
            response = self.get_response(request)
            return response
        finally:
            # 3. Limpieza OBLIGATORIA (Se ejecuta SÍ o SÍ, incluso si ocurren excepciones)
            _thread_locals.user = None