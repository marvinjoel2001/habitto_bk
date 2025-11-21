# 🔑 Usuarios y Contraseñas del Sistema

Este archivo contiene los usuarios generados por el script de población de datos para facilitar las pruebas del sistema.

## 📋 Credenciales de Acceso

**Contraseña por defecto para TODOS los usuarios:** `sistemas123`

### 🏠 Propietarios
| Usuario | Email | Nombre Completo | Tipo |
|---------|--------|------------------|------|
| `carlos_mendoza` | carlos.m@email.com | Carlos Mendoza | Propietario |
| `maria_rodriguez` | maria.r@email.com | María Rodríguez | Propietario |
| `juan_perez` | juan.p@email.com | Juan Pérez | Propietario |
| `ana_gomez` | ana.g@email.com | Ana Gómez | Propietario |

### 👥 Inquilinos que Buscan Roomie
| Usuario | Email | Nombre Completo | Tipo |
|---------|--------|------------------|------|
| `laura_silva` | laura.s@email.com | Laura Silva | Busca Roomie |
| `pedro_ramirez` | pedro.r@email.com | Pedro Ramírez | Busca Roomie |
| `sofia_torres` | sofia.t@email.com | Sofía Torres | Busca Roomie |
| `diego_morales` | diego.m@email.com | Diego Morales | Busca Roomie |

### 🏠 Inquilinos Normales
| Usuario | Email | Nombre Completo | Tipo |
|---------|--------|------------------|------|
| `andrea_flores` | andrea.f@email.com | Andrea Flores | Inquilino |
| `miguel_castro` | miguel.c@email.com | Miguel Castro | Inquilino |
| `valentina_rios` | valentina.r@email.com | Valentina Ríos | Inquilino |
| `alejandro_suarez` | alejandro.s@email.com | Alejandro Suárez | Inquilino |

### 🏢 Agentes Inmobiliarios
| Usuario | Email | Nombre Completo | Tipo |
|---------|--------|------------------|------|
| `roberto_vargas` | roberto.v@email.com | Roberto Vargas | Agente |
| `claudia_mendez` | claudia.m@email.com | Claudia Méndez | Agente |

## 🚀 Cómo Usar

### Autenticación JWT
```bash
# Obtener token para cualquier usuario
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "laura_silva",
    "password": "sistemas123"
  }'
```

### Probar Endpoints de Roomie
```bash
# Obtener propiedades incluyendo roomie seekers
curl -X GET "http://localhost:8000/api/properties/?include_roomies=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Obtener roomies disponibles
curl -X GET "http://localhost:8000/api/roomie_search/available/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Obtener todos los roomie seekers
curl -X GET "http://localhost:8000/api/roomie_search/all-seekers/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎯 Usuarios Recomendados para Pruebas

### Para probar Roomie Matching:
- **Laura Silva** (`laura_silva`) - Busca roomie con presupuesto $300-800
- **Pedro Ramírez** (`pedro_ramirez`) - Busca roomie con presupuesto $300-800
- **Carlos Mendoza** (`carlos_mendoza`) - Propietario con propiedades que permiten roomies

### Para probar Matches:
1. Logueate como Laura Silva
2. Dale like a una propiedad de Carlos Mendoza
3. Logueate como Carlos Mendoza y acepta el match
4. La propiedad se convertirá automáticamente en roomie listing

## 📊 Resumen de Datos Creados

- **5 Zonas** de Santa Cruz
- **9 Métodos de Pago**
- **15 Amenidades**
- **11 Usuarios** con perfiles completos
- **15 Propiedades** con características variadas
- **Reseñas, mensajes y notificaciones** para pruebas

## 🔄 Recargar Datos

Si necesitas recargar los datos:
```bash
python manage.py populate_realistic_data --delete-existing
```

**Nota:** Esto eliminará todos los datos existentes y los recreará desde cero.
