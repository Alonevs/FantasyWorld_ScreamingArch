-- Aplicar cambios de Timeline manualmente
BEGIN;

-- 1. Añadir campo change_type
ALTER TABLE "caos_versions" ADD COLUMN "change_type" varchar(20) DEFAULT 'LIVE' NOT NULL;

-- 2. Añadir campo timeline_year
ALTER TABLE "caos_versions" ADD COLUMN "timeline_year" integer NULL;

-- 3. Añadir campo proposed_snapshot
ALTER TABLE "caos_versions" ADD COLUMN "proposed_snapshot" jsonb NULL;

-- 4. Crear índice para change_type y status
CREATE INDEX "idx_change_type_status" ON "caos_versions" ("change_type", "status");

-- 5. Crear índice para timeline_year
CREATE INDEX "idx_timeline_year" ON "caos_versions" ("timeline_year");

-- 6. Añadir constraint para timeline_year
ALTER TABLE "caos_versions" ADD CONSTRAINT "timeline_year_required_for_timeline" 
CHECK (
    ("change_type" = 'TIMELINE' AND "timeline_year" IS NOT NULL) OR 
    ("change_type" IN ('LIVE', 'METADATA') AND "timeline_year" IS NULL)
);

-- 7. Añadir constraint para proposed_snapshot
ALTER TABLE "caos_versions" ADD CONSTRAINT "proposed_snapshot_required_for_timeline" 
CHECK (
    ("change_type" = 'TIMELINE' AND "proposed_snapshot" IS NOT NULL) OR 
    ("change_type" IN ('LIVE', 'METADATA'))
);

COMMIT;
