# Narrative Workflow & Visibility

This document outlines the lifecycle of narratives (Lore, Stories, Chapters) in FantasyWorld, including the creation process, approval workflow, and visibility rules.

## 1. Creation Process

### Initial Draft (Version 0)
When a user starts creating a narrative (or sub-chapter), the system immediately creates a **Draft** container.
-   **Status**: `current_version_number = 0`
-   **Visibility**: Hidden from public lists. Visible only to the author and admins via the Dashboard.
-   **Content**: Placeholder content is used initially.

### Proposal (Version 1)
The actual content provided by the user (Title, Body) is saved as a **Proposal** (`CaosNarrativeVersionORM`).
-   **Version**: 1
-   **Status**: `PENDING`
-   **Action**: `ADD`

## 2. Approval Workflow

All new narratives and changes must be approved via the **Dashboard**.

### Approval -> Auto-Publish
When an admin (or authorized user) approves a narrative proposal:
1.  The `CaosNarrativeVersionORM` status changes to `APPROVED`.
2.  **Auto-Publish**: The system automatically applies the changes to the live `CaosNarrativeORM` and sets `current_version_number` to the new version.
3.  The narrative becomes **Live** and visible to everyone.

### Rejection -> Cleanup
If a **Creation Proposal** (Action: `ADD`) is rejected:
1.  The `CaosNarrativeVersionORM` status changes to `REJECTED`.
2.  **Cleanup**: The system automatically **deletes** the parent `CaosNarrativeORM` draft.
3.  This prevents "ghost drafts" from cluttering the database and dashboard.

## 3. Visibility Rules

To ensure a clean reading experience, strict visibility rules are enforced:

### World Index
-   **Live Narratives**: Visible to everyone.
-   **Drafts (v0)**: **Hidden**. They do not appear in the list, even for the author.

### Narrative Viewer (Sub-Chapters)
-   **Live Chapters**: Visible to everyone in the "Sub-Chapters" list.
-   **Draft Chapters**: **Hidden**. They do not appear in the list.

### Dashboard
-   **Drafts & Proposals**: The Dashboard is the **exclusive** place for authors to view and manage their pending work.
