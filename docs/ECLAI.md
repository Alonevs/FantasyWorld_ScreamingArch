# ECLAI: AI Integration Guide

## 🤖 Overview
**ECLAI** (Engine for Creative LLM & AI) is the module responsible for integrating Artificial Intelligence into FantasyWorld. It currently supports:
-   **Text Generation**: Using LLMs (like Llama) to generate lore, descriptions, and narrative content.
-   **Image Generation**: Using Stable Diffusion to visualize worlds, characters, and scenes.

## 🖼️ Image Generation Flow

### 1. Generation
The user provides a prompt (e.g., "A floating island with waterfalls"). The system sends this to the Stable Diffusion service (`sd_service.py`).

### 2. Staging Area
Generated images are NOT immediately saved to the world. They are placed in a **Staging Area** (client-side or temporary storage). This allows the user to generate multiple options and pick the best one.

### 3. Proposal
When the user selects an image, it is submitted as a **Proposal**. It creates a `CaosImageProposal` (or similar mechanism linked to `CaosVersionORM`).

### 4. Approval
An admin (or the user themselves) reviews the proposal in the **Dashboard**.
-   **Approve**: The image becomes the official cover/illustration for the entity.
-   **Reject**: The image is discarded.

## 🧠 Text Generation (Planned)
Future updates will enhance the text generation capabilities:
-   **Context Awareness**: The AI will be aware of the world's existing lore to generate consistent content.
-   **Interactive Chat**: A "Wizard" mode to help users brainstorm ideas.

## 🛠️ Configuration
AI settings are configured in `src/Infrastructure/DjangoFramework/config/settings.py`. You may need to provide API keys or local endpoints for the AI services.