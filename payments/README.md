# Módulo de Pagos (BNB QR Simple)

## Configuración en `settings.py`

```python
# bk_habitto/settings.py

BNB_QR = {
    'BASE_URL': 'http://test.bnb.com.bo/',  # Cambiar a PROD cuando exista
    'ACCOUNT_ID': 's9CG8FE7Id75ef2jeX9bUA==',
    'INITIAL_AUTH_ID': '713K7PvTlACs1gdmv9jGgA==',
    'CURRENT_AUTH_ID': 'TuClaveSegura15*',  # La que seteaste con UpdateCredentials
    'DESTINATION_ACCOUNT_ID': '1',  # Opcional
}

INSTALLED_APPS += [
    # ...
    'payments',
]
```

## URLs

```python
# bk_habitto/urls.py
from django.urls import path, include

urlpatterns = [
    # ...
    path('payments/', include('payments.urls')),
]
```

## Vista de ejemplo para generar QR

- POST `~/payments/bnb/generate-qr`
  - Body JSON: `{ "amount": 50.00, "description": "Pedido #123", "single_use": true, "expiration_minutes": 30, "additional_data": "order_id:123" }`
  - Respuesta: `{ "qr_id": "...", "qr_base64": "..." }`

## Webhook de notificaciones

- POST `~/payments/bnb/notify`
  - Body JSON: `QRId, Gloss, sourceBankId, originName, voucherId, TransactionDateTime, additionalData`
  - Responde siempre `{ "success": true, "message": "OK" }`

## Uso directo en servicios

```python
from payments.providers.bnb_qr import BNBQRProvider

provider = BNBQRProvider()
qr_data = provider.generate_payment(
    amount=50.00,
    description="Pedido #123",
    single_use=True,
    expiration_minutes=30,
    additional_data="order_id:123",
)
# qr_data = { 'qr_id': '...', 'qr_base64': '...', 'image_bytes': b'...' }
```

