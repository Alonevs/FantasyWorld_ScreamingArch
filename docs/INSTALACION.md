# Guía de Instalación y Configuración

## Requisitos Previos
-   Python 3.10 o superior.
-   PostgreSQL 14+ (Opcional, pero recomendado para producción).
-   Git.

## Pasos de Instalación

1.  **Clonar y Entorno Virtual**:
    ```powershell
    git clone https://github.com/Alonevs/FantasyWorld_ScreamingArch.git
    cd FantasyWorld_ScreamingArch
    python -m venv venv
    .\venv\Scripts\activate
    ```

2.  **Dependencias**:
    ```powershell
    pip install -r requirements.txt
    ```

3.  **Configuración de Entorno (.env)**:
    Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:
    ```ini
    DEBUG=True
    SECRET_KEY=tu_clave_secreta_aqui
    
    # Configuración Base de Datos (PostgreSQL)
    # Si usas SQLite, comenta estas líneas y Django usará db.sqlite3 por defecto.
    DB_NAME=nombre_bd
    DB_USER=usuario
    DB_PASSWORD=contraseña
    DB_HOST=localhost
    DB_PORT=5432
    ```

4.  **Base de Datos**:
    -   Asegúrate de que la BD PostgreSQL exista (`createdb nombre_bd`).
    -   Ejecuta las migraciones:
    ```powershell
    python src/Infrastructure/DjangoFramework/manage.py migrate
    ```

5.  **Ejecutar Servidor**:
    ```powershell
    python src/Infrastructure/DjangoFramework/manage.py runserver
    ```

## Drivers de PostgreSQL en Windows
Si tienes errores como `Error loading psycopg2`, asegúrate de tener instalada la versión binaria:
```bash
pip install "psycopg[binary]" psycopg2-binary
```
Asegúrate de instalarlo **dentro** del entorno virtual activo.
