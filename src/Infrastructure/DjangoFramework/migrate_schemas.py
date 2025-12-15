
from src.Infrastructure.DjangoFramework.persistence.models import MetadataTemplate
from src.WorldManagement.Caos.Domain.metadata import METADATA_SCHEMAS

def migrate():
    print("🚀 Iniciando migración de esquemas a base de datos...")
    
    count = 0
    for key, data in METADATA_SCHEMAS.items():
        # Clean Key: "PLANETA_SCHEMA" -> "PLANETA"
        entity_type = key.replace('_SCHEMA', '')
        
        # Schema Definition (Campos Fijos)
        schema_def = data.get('campos_fijos', {})
        
        # UI Config (Campos IA Extra can go here or in schema)
        ui_config = {
            "extra_fields": data.get('campos_ia_extra', []),
            "description": data.get('description', f"Esquema para {entity_type}")
        }
        
        obj, created = MetadataTemplate.objects.update_or_create(
            entity_type=entity_type,
            defaults={
                'schema_definition': schema_def,
                'ui_config': ui_config
            }
        )
        status = "✨ Creado" if created else "🔄 Actualizado"
        print(f"[{status}] {entity_type}")
        count += 1

    print(f"✅ Migración completada. {count} esquemas procesados.")

if __name__ == "__main__":
    migrate()
