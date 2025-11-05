from rest_framework.views import exception_handler as drf_exception_handler


def wrapped_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        return response

    # Keep original detail under data, provide a uniform message
    detail = response.data

    # Derive a simple message
    default_message = 'Error interno del servidor'
    status = getattr(response, 'status_code', 500)
    if status == 400:
        default_message = 'Datos inválidos'
    elif status == 401:
        default_message = 'Token de autenticación requerido'
    elif status == 403:
        default_message = 'Permiso denegado'
    elif status == 404:
        default_message = 'Recurso no encontrado'
    elif 400 < status < 500:
        default_message = 'Error de solicitud'

    response.data = {
        'success': False,
        'message': default_message,
        'data': detail,
    }

    return response