from rest_framework.renderers import JSONRenderer


class WrappedJSONRenderer(JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # If there's no context (shouldn't happen in DRF), fallback
        if renderer_context is None:
            return super().render(data, accepted_media_type, renderer_context)

        response = renderer_context.get('response')
        request = renderer_context.get('request')

        # If the response is already in wrapped format, respect it
        if isinstance(data, dict) and ('success' in data and 'data' in data):
            return super().render(data, accepted_media_type, renderer_context)

        status_code = getattr(response, 'status_code', 200)

        # Determine default message by method
        default_messages = {
            'GET': 'Operación exitosa',
            'POST': 'Creado exitosamente',
            'PUT': 'Actualizado exitosamente',
            'PATCH': 'Actualizado exitosamente',
            'DELETE': 'Eliminado exitosamente',
        }
        method = getattr(request, 'method', 'GET') if request else 'GET'
        message = default_messages.get(method, 'Operación exitosa')

        # Override message if view set a custom one
        custom_message = getattr(response, '_drf_message', None)
        if custom_message:
            message = custom_message

        # Success responses (2xx)
        if 200 <= status_code < 300:
            wrapped = {
                'success': True,
                'message': message,
                'data': data,
            }
            return super().render(wrapped, accepted_media_type, renderer_context)

        # Error responses: let exception handler define structure where possible
        # If not already wrapped, wrap here
        if isinstance(data, dict) and ('success' in data and data.get('success') is False):
            return super().render(data, accepted_media_type, renderer_context)

        wrapped_error = {
            'success': False,
            'message': 'Error de solicitud',
            'data': data,
        }
        return super().render(wrapped_error, accepted_media_type, renderer_context)