from rest_framework.views import APIView


class MessageConfigMixin(APIView):
    """
    Mixin para inyectar mensajes de éxito específicos por acción en la respuesta.
    Define un diccionario "success_messages" por vista con claves de acción
    (list, retrieve, create, update, partial_update, destroy y acciones personalizadas)
    y valores de texto del mensaje.
    """

    # Dict opcional a definir en cada ViewSet
    success_messages = {}

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        try:
            # Solo inyectar para respuestas exitosas
            status_code = getattr(response, 'status_code', 200)
            if 200 <= status_code < 300:
                action = getattr(self, 'action', None)
                messages_map = getattr(self, 'success_messages', {}) or {}

                msg = None
                if action:
                    msg = messages_map.get(action)

                # Fallback por método HTTP si no hay mensaje por acción
                if not msg:
                    method_key = request.method.lower() if request and hasattr(request, 'method') else 'get'
                    msg = messages_map.get(method_key)

                if msg:
                    setattr(response, '_drf_message', msg)
        except Exception:
            # No romper el flujo por errores de mensaje
            pass

        return response

    # Helper opcional para acciones personalizadas
    @staticmethod
    def set_response_message(response, message: str):
        setattr(response, '_drf_message', message)
        return response