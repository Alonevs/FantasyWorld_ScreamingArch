# Architecture Guide: Screaming Architecture + Django

## 🏗️ Philosophy
This project follows the **Screaming Architecture** principle (also known as Clean Architecture). The core idea is that the directory structure should "scream" what the application *does* (its domain), rather than the framework it uses.

In our case, the domain is **WorldManagement** (managing fantasy worlds), and the detail is **Django** (the web framework).

## 📂 Directory Structure

### `src/WorldManagement` (The Core)
This directory contains the **Domain** and **Application** layers. It should be (mostly) framework-agnostic.
-   **Domain/**: Contains Entities (`World`, `Narrative`) and Value Objects. These are pure Python classes representing the business concepts.
-   **Application/**: Contains Use Cases (e.g., `CreateWorld`, `UpdateNarrative`). These orchestrate the flow of data and business rules.
-   **Infrastructure/**: Contains implementations of interfaces defined in the Domain (e.g., `DjangoCaosRepository` which implements `CaosRepository`).

### `src/Infrastructure/DjangoFramework` (The Detail)
This directory contains the **Infrastructure** layer specific to Django.
-   **config/**: Standard Django `settings.py`, `urls.py`, etc.
-   **persistence/**:
    -   **models.py**: Django ORM models (`CaosWorldORM`, `CaosNarrativeORM`). These are *persistence concerns*, not domain entities.
    -   **views/**: Django views that handle HTTP requests. They call Use Cases from the Application layer.
    -   **templates/**: HTML templates for the UI.

## 🔄 Data Flow
1.  **User Request**: A user clicks a button in the browser.
2.  **View**: A Django View receives the request.
3.  **Use Case**: The View instantiates a Use Case (e.g., `CreateNarrativeUseCase`) and passes the necessary data.
4.  **Repository**: The Use Case interacts with a Repository Interface (e.g., `CaosRepository`).
5.  **ORM**: The Repository Implementation (`DjangoCaosRepository`) translates the domain request into a Django ORM query (`CaosNarrativeORM`).
6.  **Database**: The data is saved/retrieved from the database.
7.  **Response**: The data flows back up, converted to Domain Entities, then to View Models, and finally rendered in a Template.

## 🧩 Key Patterns
-   **Repository Pattern**: Decouples the domain from the database. We use `CaosRepository` (interface) and `DjangoCaosRepository` (implementation).
-   **Versioning**: We use a "Draft/Live" system. Changes are saved as `CaosVersionORM` (proposals) and must be approved to become "Live" data.
-   **NanoIDs**: We are transitioning to NanoIDs for public-facing URLs to avoid exposing database auto-increment IDs.