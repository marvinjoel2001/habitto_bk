from __future__ import annotations

import json
import logging
from typing import Any, Dict

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from payments.providers.bnb_qr import BNBQRProvider, BNBAPIError


logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def receive_notification(request: HttpRequest):
    """Webhook de notificación de pagos de BNB.

    Espera JSON con: QRId, Gloss, sourceBankId, originName, voucherId,
    TransactionDateTime, additionalData.

    Responde siempre `{"success": True, "message": "OK"}`.
    """

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        logger.warning('Notificación con body inválido')
        return JsonResponse({'success': True, 'message': 'OK'})

    qr_id = payload.get('QRId') or payload.get('qrId')
    gloss = payload.get('Gloss') or payload.get('gloss')
    voucher_id = payload.get('voucherId')
    tx_datetime = payload.get('TransactionDateTime')
    additional = payload.get('additionalData')

    # TODO: Validaciones adicionales (IP, secreto) si aplica.

    # Procesamiento de pago: localizar orden por `qr_id` o `gloss`.
    # Este proyecto no define un modelo Order; de ejemplo, se podría
    # buscar un Payment pendiente y marcarlo pagado utilizando metadata
    # codificada en `additionalData`.
    try:
        logger.info('Pago recibido: qr_id=%s gloss=%s voucher=%s at=%s add=%s', qr_id, gloss, voucher_id, tx_datetime, additional)
        # Ejemplo: disparar signal o tarea asíncrona
        # process_payment.delay(qr_id=qr_id, gloss=gloss, voucher=voucher_id, meta=additional)
    except Exception:
        logger.exception('Error procesando notificación BNB')

    return JsonResponse({'success': True, 'message': 'OK'})


@csrf_exempt
@require_POST
def generate_qr_view(request: HttpRequest):
    """Endpoint de ejemplo para generar un QR.

    Body JSON:
        amount: float
        description: str
        single_use: bool (opcional)
        expiration_minutes: int (opcional)
        additional_data: str (opcional)

    Respuesta:
        {"qr_id": "...", "qr_base64": "..."}
    """

    try:
        data: Dict[str, Any] = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    amount = float(data.get('amount', 0))
    description = str(data.get('description', ''))
    single_use = bool(data.get('single_use', True))
    expiration_minutes = data.get('expiration_minutes')
    additional_data = data.get('additional_data')

    if not amount or not description:
        return JsonResponse({'error': 'amount y description son requeridos'}, status=400)

    provider = BNBQRProvider()
    try:
        qr = provider.generate_payment(
            amount=amount,
            description=description,
            single_use=single_use,
            expiration_minutes=expiration_minutes,
            additional_data=additional_data,
        )
        return JsonResponse({'qr_id': qr['qr_id'], 'qr_base64': qr['qr_base64']})
    except BNBAPIError as e:
        return JsonResponse({'error': str(e)}, status=502)
    except Exception:
        logger.exception('Error generando QR')
        return JsonResponse({'error': 'Error interno'}, status=500)

