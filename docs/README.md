# Developer Documentation

## 🛠️ Environment Setup

### 1. Python Environment
Ensure you have Python 3.10+ installed.
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Database
The project uses SQLite by default for development.
```bash
python src/Infrastructure/DjangoFramework/manage.py migrate
```

### 3. Static Files & Tailwind
The project uses Tailwind CSS. You may need to install Node.js dependencies if you plan to modify styles.
```bash
cd src/Infrastructure/DjangoFramework/theme/static_src
npm install
npm run dev  # Watch mode
```

## 🧪 Testing
Run the test suite to ensure everything is working correctly.
```bash
python src/Infrastructure/DjangoFramework/manage.py test src.Infrastructure.DjangoFramework.persistence.tests
```

## 📝 Code Style
-   **Python**: Follow PEP 8.
-   **Imports**: Sort imports using `isort` or similar.
-   **Architecture**: STRICTLY follow the Screaming Architecture. Do not import Django models directly into the Domain layer.

## 📚 Documentation Index
-   [Architecture Guide](ARCHITECTURE.md): Screaming Architecture principles and directory structure.
-   [AI Integration (ECLAI)](ECLAI.md): Details on the AI module for text and image generation.
-   [Narrative Workflow](NARRATIVE_WORKFLOW.md): Rules for creation, approval, and visibility of narratives.

## 🚀 Deployment
(Add deployment instructions here, e.g., Docker, Gunicorn, Nginx)