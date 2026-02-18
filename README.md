# News Scraper System

Sistema integral y robusto en Python para la extracción, gestión y consulta de noticias desde feeds RSS de periódicos. El sistema es modular, configurable y está expuesto a través de una API REST con FastAPI.

## Características

- **Scraping de Feeds**: Soporte para múltiples feeds RSS/Atom configurables.
- **Extracción Inteligente**: Uso de `trafilatura` y `BeautifulSoup` para extraer el contenido principal, títulos e imágenes de los artículos.
- **Control de Duplicados**: Evita duplicados por URL y por dominio.
- **Persistencia**: Almacenamiento en base de datos SQLite y exportación a archivos JSON.
- **API REST**: Endpoints síncronos para iniciar el scraping, listar noticias de hoy, leer detalles y marcar noticias como usadas.
- **Dockerizado**: Fácil despliegue con Docker y Docker Compose, incluyendo tareas programadas con Cron.

## Estructura del Proyecto

```text
news-scraper/
├── config/           # Configuración de feeds (feeds.json)
├── data/             # Base de datos SQLite
├── logs/             # Logs de ejecución de Cron
├── output/           # Artículos extraídos en JSON e imágenes
├── api.py            # API REST con FastAPI
├── scraper.py        # Orquestador del proceso de scraping
├── feed_reader.py    # Módulo de lectura de feeds
├── article_scraper.py # Módulo de extracción de artículos
├── storage.py        # Módulo de persistencia
├── Dockerfile        # Configuración de la imagen Docker
└── docker-compose.yml # Orquestación de contenedores
```

## Instalación y Ejecución

### Con Docker (Recomendado)

1. Clonar el repositorio.
2. Crear un archivo `.env` basado en `.env.example` y ajustar las variables si es necesario.
3. Ejecutar:
   ```bash
   docker-compose up -d --build
   ```

### Localmente

1. Crear un entorno virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar la API:
   ```bash
   uvicorn api:app --host 0.0.0.0 --port 8000
   ```

## API Documentation

Una vez iniciada la API, puedes acceder a la documentación interactiva en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
