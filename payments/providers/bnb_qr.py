from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.utils import timezone

from .base import PaymentProvider
from .exceptions import BNBAPIError, BNBAuthError
from payments.utils import decode_base64_image


logger = logging.getLogger(__name__)


@dataclass
class _TokenCache:
    token: Optional[str] = None
    expires_at: Optional[float] = None


class BNBQRProvider(PaymentProvider):
    """Proveedor BNB Pago QR Simple.

    Configuración vía `settings.BNB_QR`:

    BNB_QR = {
        'BASE_URL': 'http://test.bnb.com.bo/',
        'ACCOUNT_ID': '...',
        'INITIAL_AUTH_ID': '...',
        'CURRENT_AUTH_ID': '...',
        'DESTINATION_ACCOUNT_ID': '1',
    }
    """

    def __init__(self) -> None:
        cfg = getattr(settings, 'BNB_QR', None)
        if not cfg or 'BASE_URL' not in cfg or 'ACCOUNT_ID' not in cfg:
            raise ValueError('Configuración BNB_QR inválida en settings.py')
        self.base_url: str = cfg['BASE_URL'].rstrip('/')
        self.account_id: str = cfg['ACCOUNT_ID']
        self.current_auth_id: Optional[str] = cfg.get('CURRENT_AUTH_ID')
        self.initial_auth_id: Optional[str] = cfg.get('INITIAL_AUTH_ID')
        self.destination_account_id: Optional[str] = cfg.get('DESTINATION_ACCOUNT_ID')
        self._cache = _TokenCache()

    # --- Autenticación -----------------------------------------------------
    def _get_token(self, force_refresh: bool = False) -> str:
        """Obtiene y cachea token JWT del BNB.

        Si `force_refresh` es True, solicita un token nuevo ignorando cache.
        Asume expiración de 3600 segundos si la respuesta no incluye TTL.
        """

        now = time.time()
        if not force_refresh and self._cache.token and self._cache.expires_at and now < self._cache.expires_at:
            return self._cache.token

        if not self.current_auth_id:
            raise BNBAuthError('CURRENT_AUTH_ID no configurado. Ejecuta update_credentials primero.')

        url = f"{self.base_url}/auth/token"
        payload = {
            'accountId': self.account_id,
            'currentAuthId': self.current_auth_id,
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
        except requests.RequestException as e:
            logger.exception('Error de red solicitando token BNB')
            raise BNBAuthError(f'Fallo de red al obtener token: {e}')

        if resp.status_code != 200:
            logger.error('Fallo autenticación BNB: %s %s', resp.status_code, resp.text)
            raise BNBAuthError(f'HTTP {resp.status_code} al obtener token')

        data = resp.json()
        token = data.get('token') or data.get('access_token')
        if not token:
            raise BNBAuthError('Respuesta sin token')

        ttl = data.get('expires_in') or 3600
        self._cache.token = token
        self._cache.expires_at = time.time() + int(ttl) - 30
        return token

    def update_credentials(self, new_auth_id: str) -> Dict[str, Any]:
        """Actualiza la credencial inicial en el BNB.

        Debe usarse la primera vez para establecer `CURRENT_AUTH_ID` o cuando se
        requiera rotar la clave.
        """

        url = f"{self.base_url}/auth/UpdateCredentials"
        payload = {
            'accountId': self.account_id,
            'initialAuthId': self.initial_auth_id,
            'newAuthId': new_auth_id,
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
        except requests.RequestException as e:
            logger.exception('Error de red en UpdateCredentials')
            raise BNBAPIError(f'Fallo de red en UpdateCredentials: {e}')

        data = _safe_json(resp)
        if resp.status_code != 200 or not data.get('success', True):
            logger.error('UpdateCredentials falló: %s %s', resp.status_code, data)
            raise BNBAPIError('UpdateCredentials no exitoso')

        # Actualiza en memoria; persistir en settings/secret es manual.
        self.current_auth_id = new_auth_id
        # Fuerza invalidación de token existente.
        self._cache = _TokenCache()
        return data

    # --- Operaciones QR ----------------------------------------------------
    def generate_payment(
        self,
        amount: float,
        description: str,
        *,
        single_use: bool = True,
        expiration_minutes: Optional[int] = None,
        additional_data: Optional[str] = None,
        destination_account_id: Optional[str] = None,
        currency: str = 'BOB',
    ) -> Dict[str, Any]:
        """Genera un QR con imagen.

        Returns:
            {'qr_id': str, 'qr_base64': str, 'image_bytes': bytes}
        """

        token = self._get_token()
        url = f"{self.base_url}/QRSimple.API/api/v1/main/getQRWithImageAsync"

        expiration_str: Optional[str] = None
        if expiration_minutes is not None:
            dt = timezone.now() + timezone.timedelta(minutes=expiration_minutes)
            expiration_str = dt.strftime('%Y-%m-%d %H:%M:%S')

        payload: Dict[str, Any] = {
            'currency': currency,
            'gloss': description,
            'amount': amount,
            'singleUse': single_use,
        }
        if expiration_str:
            payload['expirationDate'] = expiration_str
        if additional_data:
            payload['additionalData'] = additional_data
        if destination_account_id or self.destination_account_id:
            payload['destinationAccountId'] = destination_account_id or self.destination_account_id

        headers = {'Authorization': f'Bearer {token}'}
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code == 401:
            headers['Authorization'] = f'Bearer {self._get_token(force_refresh=True)}'
            resp = requests.post(url, json=payload, headers=headers, timeout=30)

        data = _safe_json(resp)
        if resp.status_code != 200 or not data.get('success', False):
            logger.error('Generación de QR falló: %s %s', resp.status_code, data)
            raise BNBAPIError(data.get('message') or 'Error generando QR')

        qr_id = data.get('id') or data.get('qrId')
        qr_b64 = data.get('qr')
        if not qr_id or not qr_b64:
            raise BNBAPIError('Respuesta sin id/qr')

        image_bytes = decode_base64_image(qr_b64)
        return {'qr_id': qr_id, 'qr_base64': qr_b64, 'image_bytes': image_bytes}

    def get_qr_status(self, qr_id: str) -> Dict[str, Any]:
        """Obtiene estado de un QR generado."""

        token = self._get_token()
        url = f"{self.base_url}/QRSimple.API/api/v1/main/getQRStatus"
        headers = {'Authorization': f'Bearer {token}'}
        resp = requests.post(url, json={'qrId': qr_id}, headers=headers, timeout=30)
        if resp.status_code == 401:
            headers['Authorization'] = f'Bearer {self._get_token(force_refresh=True)}'
            resp = requests.post(url, json={'qrId': qr_id}, headers=headers, timeout=30)

        data = _safe_json(resp)
        if resp.status_code != 200 or not data.get('success', False):
            raise BNBAPIError(data.get('message') or 'Error consultando estado del QR')
        return data

    def list_qrs_by_date(self, date: str) -> Dict[str, Any]:
        """Lista QRs por fecha (formato 'YYYY-MM-DD')."""

        token = self._get_token()
        url = f"{self.base_url}/QRSimple.API/api/v1/main/listQRByDate"
        headers = {'Authorization': f'Bearer {token}'}
        resp = requests.post(url, json={'date': date}, headers=headers, timeout=30)
        if resp.status_code == 401:
            headers['Authorization'] = f'Bearer {self._get_token(force_refresh=True)}'
            resp = requests.post(url, json={'date': date}, headers=headers, timeout=30)

        data = _safe_json(resp)
        if resp.status_code != 200 or not data.get('success', False):
            raise BNBAPIError(data.get('message') or 'Error listando QRs por fecha')
        return data

    def cancel_qr(self, qr_id: str) -> Dict[str, Any]:
        """Cancela un QR existente."""

        token = self._get_token()
        url = f"{self.base_url}/QRSimple.API/api/v1/main/cancelQR"
        headers = {'Authorization': f'Bearer {token}'}
        resp = requests.post(url, json={'qrId': qr_id}, headers=headers, timeout=30)
        if resp.status_code == 401:
            headers['Authorization'] = f'Bearer {self._get_token(force_refresh=True)}'
            resp = requests.post(url, json={'qrId': qr_id}, headers=headers, timeout=30)

        data = _safe_json(resp)
        if resp.status_code != 200 or not data.get('success', False):
            raise BNBAPIError(data.get('message') or 'Error cancelando QR')
        return data


def _safe_json(resp: requests.Response) -> Dict[str, Any]:
    try:
        return resp.json()
    except ValueError:
        return {'success': False, 'message': 'Respuesta no JSON', 'raw': resp.text, 'status_code': resp.status_code}

