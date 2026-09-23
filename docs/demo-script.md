# Guion de demostración de SecureDocs

## Preparación

1. Inicie la aplicación con `uvicorn app.main:app --reload`.
2. Abra `http://127.0.0.1:8000` y mantenga otra pestaña en `/docs`.
3. Use el contexto `PERU` y `CORPORATIVO`, que la interfaz envía automáticamente.

## Recorrido sugerido

1. Inicie sesión como `empleado@securedocs.local` y muestre que solo aparece el documento de FINANZAS.
2. Intente aprobarlo. Explique que RBAC rechaza la acción porque EMPLEADO no tiene `APPROVE_DOCUMENT`.
3. En la API, consulte el mismo documento con `X-Location: CHILE`. Muestre la denegación ABAC por país.
4. Consulte un documento de nivel 4 con `X-Device: PERSONAL`. Muestre la denegación por dispositivo.
5. Repita con `X-Access-Time: 2026-09-23T22:00:00-05:00`. Muestre la denegación por horario.
6. Inicie sesión como `supervisor@securedocs.local`, apruebe el documento y verifique que pasa a `PUBLICADO`.
7. Inicie sesión como `auditor@securedocs.local` y abra Auditoría. Señale el usuario, acción, resultado, contexto y motivo de cada intento.
8. Cierre la sesión y explique que el identificador del JWT queda revocado.

## Mensaje técnico principal

El rol responde qué puede intentar hacer el usuario. Los atributos responden si puede hacerlo sobre ese recurso y bajo ese contexto. SecureDocs exige que ambas evaluaciones permitan la solicitud y registra toda decisión.

