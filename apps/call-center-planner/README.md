# Call Center Planner (localhost)

Aplicación local para:

1. Subir un CSV/XLSX con columnas `DÍA`, `FRANJA`, `LLAMADAS`.
2. Generar previsión de llamadas a 1 año (intervalos de 30 min).
3. Calcular FTE requerido con objetivos operativos (`NDA`, `NDS`, `AHT`, `ASA`, ocupación, shrinkage, etc.).
4. Visualizar gráficas y filtrar por fechas.
5. Persistir datos en SQLite (`data/planner.db`).

## Ejecutar

```bash
cd apps/call-center-planner
python3 app.py
```

Abrir en navegador: `http://127.0.0.1:8080`

## Formatos soportados

- CSV UTF-8/Latin-1 con cabecera exacta: `DÍA,FRANJA,LLAMADAS`
- XLSX (primera hoja), con las mismas columnas.

## Fórmulas incluidas

- **Forecast anual**: promedio histórico por combinación *(día de semana + franja)* con factor de tendencia lineal diaria.
- **FTE**: cálculo por intervalo con **Erlang C**, validando simultáneamente:
  - objetivo NDS en X segundos,
  - objetivo ASA,
  - ocupación máxima,
  - y ajuste por shrinkage (absentismo + descanso + pausa visual).

## API rápida

- `POST /api/upload` (multipart `file`)
- `GET /api/history?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/forecast?start=YYYY-MM-DD&end=YYYY-MM-DD`
- `POST /api/fte` (JSON inputs operativos)
