

from src.Infrastructure.DjangoFramework.persistence.models import MetadataTemplate

TEMPLATES = [
    {
        "entity_type": "CAOS",
        "schema_definition": ["Nivel de Entropía", "Heraldo Principal", "Estado de la Realidad"]
    },
    {
        "entity_type": "ABISMO",
        "schema_definition": ["Profundidad", "Densidad Mágica", "Peligrosidad"]
    },
    {
        "entity_type": "SECTOR",
        "schema_definition": ["Coordenadas", "Facción Dominante", "Recursos Clave"]
    },
    {
        "entity_type": "GALAXIA",
        "schema_definition": ["Tipo (Espiral/Elíptica)", "Edad Estimada", "Estabilidad Política"]
    },
    {
        "entity_type": "SISTEMA",
        "schema_definition": ["Estrella Principal", "Cantidad Planetas", "Zona Habitable (Si/No)"]
    },
    {
        "entity_type": "PLANETA",
        "schema_definition": ["Clima", "Gravedad", "Atmósfera", "Población", "Nivel Tecnológico", "Nivel Mágico", "Recursos Principales"]
    }
]

print("🌱 Seeding Metadata Templates...")
for t in TEMPLATES:
    obj, created = MetadataTemplate.objects.update_or_create(
        entity_type=t["entity_type"],
        defaults={"schema_definition": t["schema_definition"]}
    )
    action = "Created" if created else "Updated"
    print(f"   - {t['entity_type']}: {action}")

print("✅ Done. Total Templates:", MetadataTemplate.objects.count())
