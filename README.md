# FantasyWorld (Screaming Architecture + Django)

## 📖 Introduction
**FantasyWorld** is a comprehensive web application for creating, managing, and simulating fantasy worlds. It leverages **Django** for its robust infrastructure and follows a **Screaming Architecture** pattern to keep the core domain logic pure and decoupled.

## 🚀 Quick Start

### Prerequisites
-   Python 3.10+
-   Virtual Environment (recommended)

### Installation
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Alonevs/FantasyWorld_ScreamingArch.git
    cd FantasyWorld_ScreamingArch
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run migrations**:
    ```bash
    python src/Infrastructure/DjangoFramework/manage.py migrate
    ```

5.  **Start the server**:
    ```bash
    python src/Infrastructure/DjangoFramework/manage.py runserver
    ```

6.  **Access the application**:
    Open your browser and navigate to `http://127.0.0.1:8000`.

## 📚 Documentation
Detailed documentation is available in the `docs/` directory:

-   [**Architecture**](docs/ARCHITECTURE.md): Explanation of the Screaming Architecture, DDD patterns, and directory structure.
-   [**AI Integration (ECLAI)**](docs/ECLAI.md): Details on the AI image generation system and proposal flow.
-   [**Project Context**](PROJECT_CONTEXT.md): High-level overview of the project's current state and features.

## 🛠️ Key Features
-   **World Management**: Create and visualize worlds (Tree Map, Hemispheres).
-   **Narrative Engine**: Write and organize lore, history, and chapters.
-   **Versioning System**: Robust proposal and approval workflow for all content changes.
-   **AI Power**: Generate images for your world using integrated AI models.

## 🤝 Contributing
Please read the [Architecture Guide](docs/ARCHITECTURE.md) before contributing to understand the separation of concerns between the Domain and Infrastructure layers.
