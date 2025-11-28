# Manual Técnico: Flujo de Reportes

## Arquitectura
- App `report` con modelos:
  - `ReportCategory(name, scope, is_active, created_at)`
  - `Report(reporter, target_type, target_user?, target_property?, category?, title, description, severity?, status, admin_notes?, created_at, updated_at)`
  - `ReportAttachment(report, file, uploaded_at)`
- Endpoints REST (DRF):
  - `GET /api/report-categories/`
  - `POST /api/reports/`, `GET /api/reports/`, `GET /api/reports/my/`
  - `POST /api/reports/{id}/add_attachment/`
  - `POST /api/reports/{id}/update_status/` (solo staff)
- Notificaciones: se usan `notification.models.Notification` al crear un reporte y al cambiar estado.

## Permisos
- `IsAuthenticated` para todas las rutas.
- `update_status` restringido a `is_staff`.
- `get_queryset`: usuarios ven solo sus reportes, admin ve todos.

## Validación y Seguridad
- Validaciones en `ReportSerializer.validate`:
  - `target_type=user` requiere `target_user`; `target_type=property` requiere `target_property`.
  - `title` obligatorio, `description` mínimo 10 caracteres.
- Protección anti-abuso: en `ReportViewSet.create` se limita a 10 reportes por hora por usuario (HTTP 429).
- Adjuntos almacenados bajo `media/report_attachments/` con asociación por FK.

## Seguimiento de Estados
- Estados: `submitted` → `in_review` → `resolved`/`rejected`.
- Acción `update_status` actualiza estado y opcionalmente `admin_notes`.
- Cada cambio genera `Notification` para el reportante.

## Admin Panel
- `ReportCategoryAdmin`: filtros por `scope`, activas.
- `ReportAdmin`: filtros por `target_type`, `status`, `category`; inlines de adjuntos.

## Integración y Extensibilidad
- Integrar puntos de acceso en UI donde existan perfiles y propiedades (botón “Reportar”).
- Categorías flexibles por `scope` (`profile`, `property`, `both`).
- Extensión futura: moderación automatizada, escalamiento, métricas.

