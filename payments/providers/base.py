from __future__ import annotations

import abc
from typing import Any, Dict


class PaymentProvider(abc.ABC):
    """Interfaz base para proveedores de pago.

    Cualquier implementación debe proveer `generate_payment` y puede añadir
    métodos auxiliares como `get_status`, `list_by_date` y `cancel`.
    """

    @abc.abstractmethod
    def generate_payment(self, amount: float, description: str, **kwargs: Any) -> Dict[str, Any]:
        """Genera una orden de pago (p.ej. QR) y retorna metadatos.

        Args:
            amount: Monto en la moneda del proveedor.
            description: Descripción o glosa del pago.
            **kwargs: Parámetros adicionales específicos del proveedor.

        Returns:
            Diccionario con datos del pago (p.ej. `qr_id`, `qr_base64`, `image_bytes`).
        """

