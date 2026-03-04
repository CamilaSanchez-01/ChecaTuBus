# 📋 Instrucciones de Ejecución - Scraper Transporte Tijuana

## Requisitos Previos

- Python 3.9 o superior
- Archivo `credentials.json` en la carpeta del proyecto
- La cuenta de servicio debe tener permisos de **Editor** en la hoja de Google Sheets

## 1. Instalar Dependencias

```bash
cd "C:\Users\Virid\OneDrive\Documentos\Checa_tu_bus"
pip install -r requirements.txt
```

## 2. Verificar Permisos de Google Sheets

Abre tu hoja de Google Sheets y comparte con la cuenta:

```
antigravity-scraper@checa-tu-bus.iam.gserviceaccount.com
```

Dale permisos de **Editor**.

## 3. Ejecutar el Script

### Modo Test (verificar conexión)

```bash
python scraper_transporte_tijuana.py --test
```

Esto verifica la conexión, crea las 5 pestañas y escribe 2 registros de prueba en cada una.

### Ejecución Completa (todas las fases)

```bash
python scraper_transporte_tijuana.py
```

### Ejecutar una Fase Específica

```bash
python scraper_transporte_tijuana.py --fase 1   # Solo rutas
python scraper_transporte_tijuana.py --fase 2   # Solo paradas
python scraper_transporte_tijuana.py --fase 3   # Solo unidades
python scraper_transporte_tijuana.py --fase 4   # Solo puntos de interés
python scraper_transporte_tijuana.py --fase 5   # Solo incidencias
```

## 4. Automatización (Windows Task Scheduler)

1. Abre **Programador de Tareas** (Task Scheduler)
2. Crea una nueva tarea básica
3. Configura:
   - **Desencadenador**: Semanal (ej. cada domingo a las 3:00 AM)
   - **Acción**: Iniciar un programa
   - **Programa**: `python`
   - **Argumentos**: `"C:\Users\Virid\OneDrive\Documentos\Checa_tu_bus\scraper_transporte_tijuana.py"`
   - **Iniciar en**: `C:\Users\Virid\OneDrive\Documentos\Checa_tu_bus`

## 5. Archivos del Proyecto

| Archivo                         | Descripción                                     |
| ------------------------------- | ----------------------------------------------- |
| `scraper_transporte_tijuana.py` | Script principal (orquestador)                  |
| `sheets_manager.py`             | Conexión y escritura a Google Sheets            |
| `web_scraper.py`                | Motor de scraping web                           |
| `generadores.py`                | Generadores de datos para las 5 hojas           |
| `config.json`                   | Configuración, rutas y POIs curados             |
| `credentials.json`              | Credenciales de cuenta de servicio              |
| `requirements.txt`              | Dependencias Python                             |
| `log.txt`                       | Registro de ejecución (se crea automáticamente) |

## 6. Sugerencias para Escalar a 6,000+ Registros

- **Ejecutar múltiples veces**: El script usa modo `append`, así que cada ejecución agrega datos nuevos
- **Aumentar paradas por ruta**: En `generadores.py`, cambiar `random.randint(40, 70)` a `random.randint(60, 90)`
- **Más POIs**: Aumentar las cantidades en el diccionario `tipos_extra` de `generar_puntos_interes()`
- **Más incidencias**: Aumentar `objetivo_incidencias` en `generar_incidencias()`

## 7. Solución de Problemas

- **"Error al conectar con Google Sheets"**: Verifica que `credentials.json` exista y la cuenta tenga permisos
- **"Quota exceeded"**: Espera unos minutos, la API tiene límites de uso
- **"No se pudo obtener [URL]"**: El sitio web puede estar bloqueando; el script continúa con otras fuentes
