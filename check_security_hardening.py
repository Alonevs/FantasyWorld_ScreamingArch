"""
Security Hardening Check - Automated Verification
Verifica que todas las funciones críticas tengan protección adecuada.
"""
import os
import re

# Funciones críticas que DEBEN estar protegidas
CRITICAL_FUNCTIONS = {
    'world_views.py': [
        'editar_mundo',
        'borrar_mundo',
    ],
    'narrative_views.py': [
        'editar_narrativa',
        'borrar_narrativa',
        'crear_nueva_narrativa',
        'crear_sub_narrativa',
    ],
    'media_views.py': [
        'borrar_foto',
        'borrar_fotos_batch',
    ],
    'dashboard/workflow.py': [
        'aprobar_propuesta',
        'rechazar_propuesta',
        'borrar_propuesta',
        'aprobar_narrativa',
        'rechazar_narrativa',
        'borrar_narrativa_version',
        'borrar_propuestas_masivo',
        'aprobar_propuestas_masivo',
        'aprobar_contribucion',
        'rechazar_contribucion',
    ],
    'dashboard/assets.py': [
        'aprobar_imagen',
        'rechazar_imagen',
        'borrar_imagen_definitivo',
        'borrar_mundo_definitivo',
        'borrar_narrativa_definitivo',
    ],
}

def check_function_protection(filepath, function_name):
    """Verifica si una función tiene @login_required o verificación manual"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar la función
    pattern = rf'(@login_required\s+)?def {function_name}\('
    match = re.search(pattern, content, re.MULTILINE)
    
    if not match:
        return 'NOT_FOUND', None
    
    has_decorator = match.group(1) is not None
    
    # Buscar verificación manual cerca de la función
    func_start = match.start()
    func_content = content[func_start:func_start+1000]  # Primeras 1000 chars
    
    has_manual_check = (
        'check_world_access' in func_content or
        'can_user_propose_on' in func_content or
        'can_user_view_world' in func_content or
        'if not request.user.is_authenticated' in func_content or
        'if not user.is_authenticated' in func_content or
        '@staff_member_required' in content[max(0, func_start-100):func_start]
    )
    
    if has_decorator:
        return 'PROTECTED_DECORATOR', '@login_required'
    elif has_manual_check:
        return 'PROTECTED_MANUAL', 'manual check'
    else:
        return 'UNPROTECTED', None

def run_security_check():
    base_path = 'src/Infrastructure/DjangoFramework/persistence/views'
    
    print("="*70)
    print("🛡️  SECURITY HARDENING CHECK")
    print("="*70)
    
    vulnerabilities = []
    protected_count = 0
    total_count = 0
    
    for file, functions in CRITICAL_FUNCTIONS.items():
        filepath = os.path.join(base_path, file)
        
        if not os.path.exists(filepath):
            print(f"\n⚠️  File not found: {file}")
            continue
        
        print(f"\n📄 {file}")
        print("-" * 70)
        
        for func in functions:
            total_count += 1
            status, detail = check_function_protection(filepath, func)
            
            if status == 'PROTECTED_DECORATOR':
                print(f"  ✅ {func:40} - {detail}")
                protected_count += 1
            elif status == 'PROTECTED_MANUAL':
                print(f"  ✅ {func:40} - {detail}")
                protected_count += 1
            elif status == 'UNPROTECTED':
                print(f"  🚨 {func:40} - UNPROTECTED!")
                vulnerabilities.append((file, func))
            else:
                print(f"  ❓ {func:40} - NOT FOUND")
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Total funciones críticas: {total_count}")
    print(f"Protegidas: {protected_count}")
    print(f"Vulnerables: {len(vulnerabilities)}")
    
    if vulnerabilities:
        print("\n🚨 VULNERABILIDADES ENCONTRADAS:")
        for file, func in vulnerabilities:
            print(f"  - {file}::{func}")
        print("\n⚠️  ACCIÓN REQUERIDA: Agregar @login_required o verificación manual")
        return False
    else:
        print("\n🎉 SISTEMA SEGURO - Todas las funciones críticas están protegidas")
        return True

if __name__ == '__main__':
    import sys
    success = run_security_check()
    sys.exit(0 if success else 1)
