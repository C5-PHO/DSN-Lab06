# Evidencia de casos de prueba

## Resultado automatizado

```text
........................                                                 [100%]
24 passed
Cobertura total: 86%
```

## Casos obligatorios

| N.º | Escenario | Resultado esperado | Evidencia |
|---:|---|---|---|
| 1 | Empleado consulta documento de su área | Permitido | RBAC y ABAC permiten |
| 2 | Empleado consulta documento de otra área | Denegado | Política `DEPARTAMENTO` |
| 3 | Supervisor aprueba documento de su área | Permitido | RBAC y ABAC permiten |
| 4 | Empleado intenta aprobar documento | Denegado por RBAC | Falta `APPROVE_DOCUMENT` |
| 5 | Usuario nivel 2 consulta documento nivel 4 | Denegado por ABAC | Política `NIVEL_SEGURIDAD` |
| 6 | Gerente elimina documento | Permitido | Permiso y atributos válidos |
| 7 | Auditor intenta modificar documento | Denegado por RBAC | Falta `UPDATE_DOCUMENT` |
| 8 | Usuario inactivo intenta acceder | Denegado | Política `ESTADO_USUARIO` |
| 9 | Documento confidencial fuera de horario | Denegado por ABAC | Política `HORARIO` |
| 10 | Documento nivel 5 desde dispositivo personal | Denegado | Política `DISPOSITIVO` |
| 11 | Invitado accede a documento público | Permitido | Externo, nivel 1 y publicado |
| 12 | Invitado accede a documento confidencial | Denegado | Política `INVITADOS` |

## Cinco casos adicionales

| N.º | Escenario | Resultado esperado |
|---:|---|---|
| 13 | Administrador elimina documento de otra área | Permitido |
| 14 | Supervisor modifica documento ajeno | Denegado por propiedad |
| 15 | Gerente modifica documento ajeno de su área | Permitido por excepción |
| 16 | Empleado consulta desde un país distinto | Denegado por país |
| 17 | Auditor consulta el registro de auditoría | Permitido |

La suite integral también verifica autenticación, filtrado de documentos, aprobación, consulta de auditoría y revocación del JWT.

```bash
python -m pip install -e '.[dev]'
pytest --cov=app --cov-report=term-missing
```

