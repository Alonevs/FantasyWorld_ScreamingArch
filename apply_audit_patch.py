import os
import sys

# Definimos las rutas relativas de los archivos a modificar
PATH_MODELS = os.path.join('src', 'Infrastructure', 'DjangoFramework', 'persistence', 'models.py')
PATH_USECASE = os.path.join('src', 'WorldManagement', 'Caos', 'Application', 'create_narrative.py')
PATH_VIEWS = os.path.join('src', 'Infrastructure', 'DjangoFramework', 'persistence', 'views.py')

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Archivo actualizado: {path}")

def patch_models():
    content = read_file(PATH_MODELS)
    
    # 1. Asegurar import User
    if "from django.contrib.auth.models import User" not in content:
        content = content.replace("from django.db import models", "from django.db import models\nfrom django.contrib.auth.models import User")

    # 2. Añadir campos a CaosNarrativeORM
    marker = "tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='LORE')"
    
    audit_fields = """
    # --- AUDITORIA ---
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='narrativas_creadas')
    updated_at = models.DateTimeField(auto_now=True)
    """
    
    if "created_by = models.ForeignKey" not in content:
        # Buscamos el lugar donde insertar (después del campo tipo o antes de created_at)
        if marker in content:
            content = content.replace(marker, marker + audit_fields)
        else:
            print("⚠️ No se encontró el punto de inserción exacto en models.py. Revisa manualmente.")
            return

    write_file(PATH_MODELS, content)

def patch_usecase():
    content = read_file(PATH_USECASE)
    
    # 1. Import User (Type hint opcional, pero bueno tenerlo)
    if "from django.contrib.auth.models import User" not in content:
        # No es estrictamente necesario en python dinámico, pero modificamos el execute signature
        pass

    # 2. Modificar firma de execute
    old_sig = "def execute(self, world_id: str, tipo_codigo: str, parent_nid: str = None) -> str:"
    new_sig = "def execute(self, world_id: str, tipo_codigo: str, parent_nid: str = None, user = None) -> str:"
    
    if old_sig in content:
        content = content.replace(old_sig, new_sig)
    
    # 3. Añadir el campo created_by en el create (padre)
    # Buscamos la creación del Capítulo
    marker_cap = "tipo=tipo_completo"
    injection = ", created_by=user"
    
    # Hay dos create(), uno para cap y otro para raiz. Reemplazamos ambos si no tienen ya created_by
    if "created_by=user" not in content:
        # Reemplazo simple: añade created_by=user antes del paréntesis de cierre del create
        # Esto es un poco frágil con regex, vamos a hacerlo buscando el contexto exacto del código actual
        
        # Bloque Capítulo
        block_cap_old = """                narrador=padre.narrador, 
                tipo=tipo_completo
            )"""
        block_cap_new = """                narrador=padre.narrador, 
                tipo=tipo_completo,
                created_by=user
            )"""
            
        # Bloque Raíz
        block_root_old = """                narrador="???", 
                tipo=tipo_completo
            )"""
        block_root_new = """                narrador="???", 
                tipo=tipo_completo,
                created_by=user
            )"""
            
        content = content.replace(block_cap_old, block_cap_new)
        content = content.replace(block_root_old, block_root_new)

    write_file(PATH_USECASE, content)

def patch_views():
    content = read_file(PATH_VIEWS)
    
    # Buscamos crear_nueva_narrativa y crear_sub_narrativa para inyectar el usuario
    
    # 1. Nueva Narrativa
    target_new = "new_nid = CreateNarrativeUseCase(repo).execute(world_id=jid, tipo_codigo=tipo_codigo)"
    replacement_new = """
        user = request.user if request.user.is_authenticated else None
        new_nid = CreateNarrativeUseCase(repo).execute(world_id=jid, tipo_codigo=tipo_codigo, user=user)"""
    
    if target_new in content:
        content = content.replace(target_new, replacement_new)
        
    # 2. Sub Narrativa
    target_sub = "new_nid = CreateNarrativeUseCase(repo).execute(world_id=None, tipo_codigo=tipo_codigo, parent_nid=parent_nid)"
    replacement_sub = """
        user = request.user if request.user.is_authenticated else None
        new_nid = CreateNarrativeUseCase(repo).execute(world_id=None, tipo_codigo=tipo_codigo, parent_nid=parent_nid, user=user)"""

    if target_sub in content:
        content = content.replace(target_sub, replacement_sub)

    write_file(PATH_VIEWS, content)

def main():
    print("🩹 Iniciando parcheo de Auditoría (CreatedBy)...")
    try:
        patch_models()
        patch_usecase()
        patch_views()
        print("\n✨ Parche aplicado con éxito.")
        print("⚠️ AHORA EJECUTA ESTO EN TU TERMINAL:")
        print("   python src/Infrastructure/DjangoFramework/manage.py makemigrations")
        print("   python src/Infrastructure/DjangoFramework/manage.py migrate")
    except FileNotFoundError as e:
        print(f"❌ Error: No encuentro el archivo {e.filename}. ¿Estás en la raíz del proyecto?")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()