# Project Context: FantasyWorld (Screaming Architecture + Django)

## Overview
**FantasyWorld** is a web-based application for managing and simulating fantasy worlds. It allows users to create worlds, define narratives, and generate AI-powered content (images and text).

The project recently migrated from a custom framework to **Django**, adopting a **Screaming Architecture** approach to keep the domain logic decoupled from the infrastructure.

## Key Modules

### 1. WorldManagement (Domain Core)
Located in `src/WorldManagement`, this module contains the business logic for:
-   **Caos System**: The core engine for managing `World` and `Narrative` entities.
-   **Versioning**: A robust system for proposing, reviewing, approving, and archiving changes to worlds and narratives.
-   **AI Integration**: Interfaces for generating content using LLMs (Llama) and Image Generators (Stable Diffusion).

### 2. Infrastructure (Django)
Located in `src/Infrastructure/DjangoFramework`, this module handles:
-   **Persistence**: Django ORM models (`CaosWorldORM`, `CaosNarrativeORM`, `CaosVersionORM`, etc.) that implement the repository pattern.
-   **Views & Templates**: The user interface, including the Dashboard, World Viewer, and Narrative Editor.
-   **Configuration**: Standard Django settings and URL routing.

## Current Features

### 🌍 World Management
-   **Creation**: Users can create new worlds with initial parameters.
-   **Visualization**: Interactive "Tree Map" and "Hemisphere" views to explore world data.
-   **Scanner**: *Placeholder feature* for future analysis tools.

### 📖 Narrative System
-   **Structure**: Narratives can be nested (Lore, History, Chapters).
-   **Editing**: Rich text editor for writing content.
-   **Navigation**: Improved navigation with "Back" and "Index" buttons.

### 📝 Version Control & Dashboard
-   **Proposals**: Changes to worlds or narratives create "Proposals" (Drafts) instead of modifying live data immediately.
-   **Review Flow**:
    -   **Pending**: Proposals waiting for review.
    -   **Approved**: Proposals accepted but not yet published to Live.
    -   **Rejected**: Proposals denied with a reason.
    -   **Archived**: Old versions kept for history.
-   **Dashboard**: A central hub to manage all these states, with bulk actions and filtering.

### 🎨 AI Image Generation
-   **Generation**: Users can generate images for worlds/narratives using prompts.
-   **Staging Area**: Generated images are held in a client-side staging area.
-   **Proposal Flow**: Users select the best images to submit as proposals.
-   **Approval**: Admins (or the user) approve these image proposals to make them official.

## Recent Major Changes
-   **Migration to Django**: Complete rewrite of the infrastructure layer.
-   **Screaming Architecture**: Reorganization of the codebase to emphasize domain intent.
-   **Versioning System**: Implementation of `CaosVersionORM` and `CaosNarrativeVersionORM` to handle the draft/live workflow.
-   **NanoID Strategy**: Plan to move towards NanoIDs for public-facing URLs (partially implemented).

## 📚 Project Documentation Map

*   [**CODE_STRUCTURE.md**](./CODE_STRUCTURE.md): Detailed explanation of **Screaming Architecture**, Clean Architecture principles, and the Django folder structure.
*   [**WORLD_LOGIC.md**](./WORLD_LOGIC.md): The core logical rules of the universe, including **J-IDs** (Hierarchical IDs), **Level Tables**, **Zero Padding**, and **Soft Delete** flows.
*   [**AI_SPECS.md**](./AI_SPECS.md): Specifications for the **AI Brain**, including Context Inheritance rules and Llama 3 Prompt Templates.
*   [**WORKFLOW.md**](./WORKFLOW.md): Detailed guide on the Approval and Versioning Workflow.
*   [**SETUP.md**](./SETUP.md): Installation and Env configuration.
*   [**TASKS.md**](./TASKS.md): Current roadmap and active todo list.

## Next Steps
-   **Refine AI Integration**: Implement the specs defined in `AI_SPECS.md`.
-   **Enhance Scanner**: Implement actual analysis logic for the "Scanner" feature.
-   **Mobile Optimization**: Improve UI responsiveness for smaller screens.
