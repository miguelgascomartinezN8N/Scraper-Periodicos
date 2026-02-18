# Manual de Usuario - News Scraper

Este documento proporciona instrucciones detalladas sobre el uso y configuración del sistema de scraping de noticias.

## 1. Configuración de Feeds

La configuración se encuentra en `config/feeds.json`. El archivo tiene dos secciones principales:

- **feeds**: Una lista de objetos que definen qué feeds RSS/Atom deben ser procesados.
  - `name`: Nombre descriptivo del feed.
  - `url`: URL del feed RSS o Atom.
  - `enabled`: Booleano para activar o desactivar el feed.
- **settings**: Configuraciones globales del scraper.
  - `request_delay_seconds`: Retraso entre solicitudes para evitar ser bloqueado.
  - `request_timeout_seconds`: Tiempo de espera máximo para cada solicitud.
  - `max_articles_per_feed`: Número máximo de artículos a procesar por cada feed en cada ejecución.
  - `user_agent`: User-Agent utilizado para las solicitudes HTTP.
  - `download_images`: Booleano para habilitar o deshabilitar la descarga local de imágenes.

## 2. Uso de la API REST

La API expone los siguientes endpoints para interactuar con el sistema:

### Scraping de Noticias
- **POST `/scrape-feeds`**: Inicia manualmente el proceso de scraping de todos los feeds habilitados. Devuelve un resumen con el número de artículos nuevos encontrados y duplicados omitidos.

### Gestión de Noticias
- **GET `/get-news-list`**: Devuelve una lista paginada de noticias que:
  - Son del día de hoy.
  - No han sido marcadas como usadas (`used=False`).
  - Parámetros: `page` (defecto 1), `page_size` (defecto 10).
- **GET `/read-full-news/{article_id}`**: Obtiene el detalle completo de una noticia específica.
- **POST `/mark-news-as-used/{article_id}`**: Marca una noticia como usada para que no vuelva a aparecer en el listado de noticias pendientes.

## 3. Automatización con Cron

En el despliegue con Docker, el sistema incluye un servicio de Cron que ejecuta el scraping automáticamente dos veces al día (9:00 AM y 9:00 PM). Puedes modificar la programación editando el archivo `crontab`.

## 4. Almacenamiento y Salida

- **Base de Datos**: Se utiliza SQLite (`data/news_scraper.db`) para la persistencia.
- **Archivos JSON**: Cada vez que se realiza un scraping, los artículos nuevos se exportan a la carpeta `output/YYYY-MM-DD/`. Se crea un archivo JSON individual por artículo y uno consolidado para todo el día.
- **Imágenes**: Si está habilitado, las imágenes se guardan en `output/images/` con un nombre basado en el hash de su URL original.

## 5. Mantenimiento y Logs

- Los logs del proceso de Cron se guardan en `logs/cron.log`.
- Puedes monitorizar el estado del contenedor con `docker logs news-scraper`.
