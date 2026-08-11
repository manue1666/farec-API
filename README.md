# Farec API

Farec API es un servicio REST desarrollado con FastAPI para gestionar usuarios, asistencias, permisos y horarios de trabajo. El sistema también incorpora verificación facial para registrar entradas y salidas mediante imágenes.

## Propósito general

La API permite:

- administrar usuarios del sistema, incluyendo sus datos básicos y conjuntos de imágenes faciales;
- registrar y consultar asistencias diarias;
- gestionar permisos de ausencia o vacaciones;
- definir horarios por usuario;
- validar identidad mediante reconocimiento facial para registrar entradas y salidas.

## Arquitectura y componentes

El proyecto está organizado en módulos separados para facilitar el mantenimiento:

- app.main: configuración de la aplicación FastAPI.
- app.api.v1.router: registro de todos los routers del API.
- app.api.v1.endpoints: endpoints para usuarios, asistencia, permisos y horarios.
- app.schemas: modelos de entrada y salida para validación de datos.
- app.models: entidades del dominio.
- app.services: lógica de negocio, incluida la verificación facial.

## Requisitos

- Python 3.10 o superior
- Dependencias listadas en requirements.txt

## Ejecución local

1. Crear y activar un entorno virtual.
2. Instalar dependencias:

   pip install -r requirements.txt

3. Ejecutar la aplicación:

   uvicorn app.main:app --reload

La API quedará disponible en:

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/api/v1/

## Base URL

Todos los endpoints de la versión actual están bajo el prefijo:

- /api/v1

## Notas generales

- Actualmente no se implementa autenticación ni autorización.
- Los errores más comunes devuelven respuestas HTTP con mensajes descriptivos.
- Los endpoints que reciben archivos esperan datos multipart/form-data.

## Modelos principales

### Usuario

Campos principales:

- email: correo electrónico del usuario.
- full_name: nombre completo.
- department: área o departamento al que pertenece.
- is_admin: indica si el usuario tiene privilegios administrativos.

Respuesta esperada en los endpoints de lectura:

- id
- email
- full_name
- department
- is_admin
- created_at

### Asistencia

Campos principales:

- user_id: identificador del usuario asociado.
- department: área asociada al registro.
- check_in: fecha y hora de entrada.
- check_out: fecha y hora de salida, opcional.
- date: fecha del registro.

Respuesta esperada en los endpoints de lectura:

- id
- user_id
- department
- check_in
- check_out
- date

### Permiso

Campos principales:

- user_id: usuario al que pertenece el permiso.
- type: tipo de permiso.
- start_date: fecha inicial.
- end_date: fecha final.
- status: estado del permiso, por defecto pending.

Respuesta esperada en los endpoints de lectura:

- id
- user_id
- type
- start_date
- end_date
- status
- created_at

### Horario

Campos principales:

- user_id: usuario asociado al horario.
- day_of_week: día de la semana, expresado como número de 0 a 6.
- start_time: hora de inicio.
- end_time: hora de finalización.

Respuesta esperada en los endpoints de lectura:

- id
- user_id
- day_of_week
- start_time
- end_time

### Resultado de verificación facial

Respuesta utilizada por los endpoints de autenticación facial:

- matched: indica si la imagen coincide con un usuario registrado.
- user_id: identificador del usuario detectado.
- face_encoding_id: identificador del encoding facial asociado.
- distance: distancia de similitud calculada.
- threshold: umbral usado en la comparación.

## Endpoints disponibles

### Usuarios

#### Listar usuarios


GET /api/v1/users

**Respuesta:**

- lista de objetos UserRead

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Lista obtenida correctamente | `[{ "id": "...", "email": "user@example.com", "full_name": "Juan Pérez", "department": "RRHH", "is_admin": false, "created_at": "2026-01-01T10:00:00" }]` |

#### Crear usuario


POST /api/v1/users
Content-Type: multipart/form-data

```text
email=juan@example.com
full_name=Juan Pérez
department=RRHH
is_admin=false
images=@foto1.jpg
images=@foto2.jpg
```

**Validaciones:**

- `email`: requerido, formato válido de email, debe ser único
- `full_name`: requerido, mínimo 1 carácter
- `department`: requerido, mínimo 1 carácter
- `images`: requerido, al menos una imagen

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 201 | Usuario creado correctamente | `{ "id": "...", "email": "juan@example.com", "full_name": "Juan Pérez", "department": "RRHH", "is_admin": false, "created_at": "2026-01-01T10:00:00" }` |
| 409 | El correo ya existe | `{ "detail": "Ya existe un usuario con ese correo" }` |
| 422 | Datos inválidos | `{ "detail": [ ... ] }` |

#### Actualizar usuario


PATCH /api/v1/users/{user_id}
Content-Type: multipart/form-data

```text
email=juan.updated@example.com
full_name=Juan Actualizado
department=TI
is_admin=true
```

**Validaciones:**

- `email`: si se envía, debe tener formato válido y ser único
- `full_name`: si se envía, debe tener al menos 1 carácter
- `department`: si se envía, debe tener al menos 1 carácter

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Usuario actualizado correctamente | `{ "id": "...", "email": "juan.updated@example.com", "full_name": "Juan Actualizado", "department": "TI", "is_admin": true, "created_at": "2026-01-01T10:00:00" }` |
| 404 | Usuario no encontrado | `{ "detail": "Usuario no encontrado" }` |
| 409 | El correo ya existe | `{ "detail": "Ya existe un usuario con ese correo" }` |

#### Eliminar usuario


DELETE /api/v1/users/{user_id}

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 204 | Usuario eliminado correctamente | Sin contenido |
| 404 | Usuario no encontrado | `{ "detail": "Usuario no encontrado" }` |

#### Agregar dataset facial


POST /api/v1/users/{user_id}/face-dataset
Content-Type: multipart/form-data

```text
images=@foto1.jpg
images=@foto2.jpg
```

**Validaciones:**

- `images`: requerido, al menos una imagen

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 201 | Muestras agregadas correctamente | `{ "user_id": "...", "stored_samples": 2 }` |
| 404 | Usuario no encontrado | `{ "detail": "Usuario no encontrado" }` |

#### Verificar rostro


POST /api/v1/users/verify-face
Content-Type: multipart/form-data

```text
image=@rostro.jpg
```

**Validaciones:**

- `image`: requerido

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Verificación completada | `{ "matched": true, "user_id": "...", "face_encoding_id": "...", "distance": 0.12, "threshold": 0.6 }` |
| 401 | No coincide con un usuario válido | `{ "detail": "No coincide con ningún usuario registrado" }` |

### Asistencia

#### Listar asistencia


GET /api/v1/attendance

**Respuesta:**

- lista de objetos AttendanceRead

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Lista obtenida correctamente | `[{ "id": "...", "user_id": "...", "department": "TI", "check_in": "2026-01-01T08:00:00", "check_out": null, "date": "2026-01-01" }]` |

#### Obtener asistencia por ID


GET /api/v1/attendance/{attendance_id}

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Registro encontrado | `{ "id": "...", "user_id": "...", "department": "TI", "check_in": "2026-01-01T08:00:00", "check_out": null, "date": "2026-01-01" }` |
| 404 | Asistencia no encontrada | `{ "detail": "Asistencia no encontrada" }` |

#### Crear asistencia manualmente


POST /api/v1/attendance
Content-Type: application/json

```json
{
  "user_id": "11111111-1111-1111-1111-111111111111",
  "department": "TI",
  "check_in": "2026-01-01T08:00:00",
  "check_out": null,
  "date": "2026-01-01"
}
```

**Validaciones:**

- `user_id`: requerido
- `department`: requerido
- `check_in`: requerido
- `date`: requerido

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 201 | Asistencia creada correctamente | `{ "id": "...", "user_id": "...", "department": "TI", "check_in": "2026-01-01T08:00:00", "check_out": null, "date": "2026-01-01" }` |
| 404 | Usuario no encontrado | `{ "detail": "Usuario no encontrado" }` |

#### Registrar entrada con rostro


POST /api/v1/attendance/check-in
Content-Type: multipart/form-data

```text
image=@rostro.jpg
```

**Validaciones:**

- `image`: requerido

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 201 | Entrada registrada correctamente | `{ "authentication": { "matched": true, "user_id": "...", "face_encoding_id": "...", "distance": 0.12, "threshold": 0.6 }, "attendance": { "id": "...", "user_id": "...", "department": "TI", "check_in": "2026-01-01T08:00:00", "check_out": null, "date": "2026-01-01" }, "action": "check_in", "message": "Entrada registrada correctamente" }` |
| 401 | Rostro no reconocido | `{ "detail": "No coincide con ningún usuario registrado" }` |
| 409 | Ya existe asistencia para hoy | `{ "detail": "Ya existe un registro de asistencia para hoy" }` |

#### Registrar salida con rostro


POST /api/v1/attendance/check-out
Content-Type: multipart/form-data

```text
image=@rostro.jpg
```

**Validaciones:**

- `image`: requerido

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Salida registrada correctamente | `{ "authentication": { "matched": true, "user_id": "...", "face_encoding_id": "...", "distance": 0.12, "threshold": 0.6 }, "attendance": { "id": "...", "user_id": "...", "department": "TI", "check_in": "2026-01-01T08:00:00", "check_out": "2026-01-01T17:00:00", "date": "2026-01-01" }, "action": "check_out", "message": "Salida registrada correctamente" }` |
| 401 | Rostro no reconocido | `{ "detail": "No coincide con ningún usuario registrado" }` |
| 404 | No existe entrada abierta | `{ "detail": "No se encontró una entrada abierta para hoy" }` |

#### Historial por usuario


GET /api/v1/attendance/users/{user_id}/history?year=2026&month=1&week=1

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Historial obtenido correctamente | `[{ "id": "...", "user_id": "...", "department": "TI", "check_in": "2026-01-01T08:00:00", "check_out": null, "date": "2026-01-01" }]` |

#### Historial por área


GET /api/v1/attendance/areas/{department}/history?year=2026&month=1&week=1

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Historial obtenido correctamente | `[{ "id": "...", "user_id": "...", "department": "TI", "check_in": "2026-01-01T08:00:00", "check_out": null, "date": "2026-01-01" }]` |

#### Actualizar asistencia


PATCH /api/v1/attendance/{attendance_id}
Content-Type: application/json

```json
{
  "check_out": "2026-01-01T17:00:00",
  "department": "RRHH"
}
```

**Validaciones:**

- `check_out`: si se envía, debe ser posterior a `check_in`
- `department`: si se envía, debe ser una cadena válida

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Asistencia actualizada correctamente | `{ "id": "...", "user_id": "...", "department": "RRHH", "check_in": "2026-01-01T08:00:00", "check_out": "2026-01-01T17:00:00", "date": "2026-01-01" }` |
| 404 | Asistencia no encontrada | `{ "detail": "Asistencia no encontrada" }` |
| 400 | Datos inconsistentes | `{ "detail": "check_out no puede ser anterior a check_in" }` |

#### Eliminar asistencia


DELETE /api/v1/attendance/{attendance_id}

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 204 | Asistencia eliminada correctamente | Sin contenido |
| 404 | Asistencia no encontrada | `{ "detail": "Asistencia no encontrada" }` |

### Permisos

#### Listar permisos


GET /api/v1/permissions

**Respuesta:**

- lista de objetos PermissionRead

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Lista obtenida correctamente | `[{ "id": "...", "user_id": "...", "type": "vacation", "start_date": "2026-01-10", "end_date": "2026-01-12", "status": "pending", "created_at": "2026-01-01T10:00:00" }]` |

#### Historial de permisos


GET /api/v1/permissions/history?user_id=...&status_filter=pending

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Historial obtenido correctamente | `[{ "id": "...", "user_id": "...", "type": "vacation", "start_date": "2026-01-10", "end_date": "2026-01-12", "status": "pending", "created_at": "2026-01-01T10:00:00" }]` |

#### Obtener permiso por ID


GET /api/v1/permissions/{permission_id}

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Permiso encontrado | `{ "id": "...", "user_id": "...", "type": "vacation", "start_date": "2026-01-10", "end_date": "2026-01-12", "status": "pending", "created_at": "2026-01-01T10:00:00" }` |
| 404 | Permiso no encontrado | `{ "detail": "Permiso no encontrado" }` |

#### Crear permiso


POST /api/v1/permissions
Content-Type: application/json

```json
{
  "user_id": "11111111-1111-1111-1111-111111111111",
  "type": "vacation",
  "start_date": "2026-01-10",
  "end_date": "2026-01-12",
  "status": "pending"
}
```

**Validaciones:**

- `user_id`: requerido
- `type`: requerido, mínimo 1 carácter
- `start_date`: requerido
- `end_date`: requerido
- `status`: opcional, si se envía debe tener al menos 1 carácter

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 201 | Permiso creado correctamente | `{ "id": "...", "user_id": "...", "type": "vacation", "start_date": "2026-01-10", "end_date": "2026-01-12", "status": "pending", "created_at": "2026-01-01T10:00:00" }` |
| 404 | Usuario no encontrado | `{ "detail": "Usuario no encontrado" }` |
| 400 | Fechas inconsistentes | `{ "detail": "end_date no puede ser anterior a start_date" }` |

#### Actualizar permiso


PATCH /api/v1/permissions/{permission_id}
Content-Type: application/json

```json
{
  "type": "medical",
  "status": "approved"
}
```

**Validaciones:**

- `type`: opcional, si se envía debe tener al menos 1 carácter
- `start_date`: opcional
- `end_date`: opcional
- `status`: opcional, si se envía debe tener al menos 1 carácter

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Permiso actualizado correctamente | `{ "id": "...", "user_id": "...", "type": "medical", "start_date": "2026-01-10", "end_date": "2026-01-12", "status": "approved", "created_at": "2026-01-01T10:00:00" }` |
| 404 | Permiso no encontrado | `{ "detail": "Permiso no encontrado" }` |
| 400 | Fechas inconsistentes | `{ "detail": "end_date no puede ser anterior a start_date" }` |

#### Eliminar permiso


DELETE /api/v1/permissions/{permission_id}

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 204 | Permiso eliminado correctamente | Sin contenido |
| 404 | Permiso no encontrado | `{ "detail": "Permiso no encontrado" }` |

### Horarios

#### Listar horarios


GET /api/v1/schedules

**Respuesta:**

- lista de objetos ScheduleRead

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Lista obtenida correctamente | `[{ "id": "...", "user_id": "...", "day_of_week": 1, "start_time": "08:00:00", "end_time": "17:00:00" }]` |

#### Obtener horario por ID


GET /api/v1/schedules/{schedule_id}

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Horario encontrado | `{ "id": "...", "user_id": "...", "day_of_week": 1, "start_time": "08:00:00", "end_time": "17:00:00" }` |
| 404 | Horario no encontrado | `{ "detail": "Horario no encontrado" }` |

#### Crear horario


POST /api/v1/schedules
Content-Type: application/json

```json
{
  "user_id": "11111111-1111-1111-1111-111111111111",
  "day_of_week": 1,
  "start_time": "08:00:00",
  "end_time": "17:00:00"
}
```

**Validaciones:**

- `user_id`: requerido
- `day_of_week`: requerido, valor entre 0 y 6
- `start_time`: requerido
- `end_time`: requerido, debe ser posterior a `start_time`

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 201 | Horario creado correctamente | `{ "id": "...", "user_id": "...", "day_of_week": 1, "start_time": "08:00:00", "end_time": "17:00:00" }` |
| 404 | Usuario no encontrado | `{ "detail": "Usuario no encontrado" }` |
| 400 | Horario inválido | `{ "detail": "end_time debe ser posterior a start_time" }` |

#### Actualizar horario


PATCH /api/v1/schedules/{schedule_id}
Content-Type: application/json

```json
{
  "day_of_week": 2,
  "start_time": "09:00:00",
  "end_time": "18:00:00"
}
```

**Validaciones:**

- `day_of_week`: opcional, valor entre 0 y 6
- `start_time`: opcional
- `end_time`: opcional, debe ser posterior a `start_time`

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 200 | Horario actualizado correctamente | `{ "id": "...", "user_id": "...", "day_of_week": 2, "start_time": "09:00:00", "end_time": "18:00:00" }` |
| 404 | Horario no encontrado | `{ "detail": "Horario no encontrado" }` |
| 400 | Horario inválido | `{ "detail": "end_time debe ser posterior a start_time" }` |

#### Eliminar horario


DELETE /api/v1/schedules/{schedule_id}

**Respuestas:**

| Status | Descripción | Respuesta |
| --- | --- | --- |
| 204 | Horario eliminado correctamente | Sin contenido |
| 404 | Horario no encontrado | `{ "detail": "Horario no encontrado" }` |
