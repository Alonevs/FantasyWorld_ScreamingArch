# 🧪 TESTING GUIDE

> **Propósito:** Guía para añadir tests cuando el proyecto lo necesite.
> **Cuándo usar:** Cuando una feature crítica se rompe frecuentemente o antes de un deploy importante.

---

## 🎯 Filosofía de Testing para Este Proyecto

**NO necesitas 100% de cobertura.** Este es un proyecto personal, no una aplicación bancaria.

**Prioriza tests para:**
1. ✅ Lógica de negocio crítica (propuestas, permisos)
2. ✅ Funciones que se rompieron antes
3. ✅ Código que cambias frecuentemente

**Ignora tests para:**
- ❌ Templates (se prueban visualmente)
- ❌ Vistas simples (CRUD básico)
- ❌ Código que "funciona y no se toca"

---

## 🚀 Setup Rápido

```bash
# Instalar pytest
pip install pytest pytest-django

# Crear archivo de configuración
# pytest.ini (en raíz del proyecto)
```

**pytest.ini:**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = src.Infrastructure.DjangoFramework.config.settings
python_files = tests.py test_*.py *_tests.py
```

---

## 📋 Tests Prioritarios

### 1. Test de Resolución de Portadas (CRÍTICO)
**Por qué:** Se rompió varias veces, lógica compleja.

```python
# tests/test_cover_detection.py
import pytest
from src.Infrastructure.DjangoFramework.persistence.utils import get_world_images

def test_cover_case_insensitive():
    """Portada debe encontrarse independiente de mayúsculas/minúsculas"""
    # Setup: crear mundo con imagen
    # ... (código de setup)
    
    imgs = get_world_images('test_world_id')
    
    # Verificar que encuentra la portada
    cover = next((i for i in imgs if i['is_cover']), None)
    assert cover is not None
    assert cover['filename'].lower() == 'test_cover.webp'.lower()

def test_cover_without_extension():
    """Portada debe encontrarse sin extensión en metadata"""
    # ... test similar
    pass

def test_cover_legacy_folder():
    """Portada debe encontrarse en carpetas legacy (ID_Name/)"""
    # ... test similar
    pass
```

---

### 2. Test de Permisos (CRÍTICO)
**Por qué:** Seguridad, no queremos que usuarios editen mundos ajenos.

```python
# tests/test_permissions.py
import pytest
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.permissions import check_ownership

def test_owner_can_edit():
    """Dueño puede editar su mundo"""
    owner = User.objects.create(username='owner')
    world = CaosWorldORM.objects.create(author=owner, name='Test')
    
    # No debe lanzar excepción
    check_ownership(owner, world)

def test_non_owner_cannot_edit():
    """Usuario random NO puede editar mundo ajeno"""
    owner = User.objects.create(username='owner')
    intruder = User.objects.create(username='intruder')
    world = CaosWorldORM.objects.create(author=owner, name='Test')
    
    # Debe lanzar excepción
    with pytest.raises(PermissionError):
        check_ownership(intruder, world)

def test_team_member_can_edit():
    """Miembro del equipo puede editar"""
    # ... test similar
    pass
```

---

### 3. Test de Flujo de Propuestas (IMPORTANTE)
**Por qué:** Lógica de negocio central.

```python
# tests/test_proposals.py
def test_create_proposal():
    """Usuario puede crear propuesta"""
    user = User.objects.create(username='user')
    world = CaosWorldORM.objects.create(name='Test')
    
    proposal = CaosVersionORM.objects.create(
        world=world,
        proposed_name='New Name',
        author=user,
        status='PENDING'
    )
    
    assert proposal.status == 'PENDING'
    assert proposal.world == world

def test_approve_proposal():
    """Admin puede aprobar propuesta"""
    # ... test de aprobación
    pass

def test_reject_proposal():
    """Admin puede rechazar propuesta"""
    # ... test de rechazo
    pass
```

---

## 🏃 Cómo Ejecutar Tests

```bash
# Todos los tests
pytest

# Solo tests de portadas
pytest tests/test_cover_detection.py

# Con output detallado
pytest -v

# Con cobertura (opcional)
pytest --cov=src/Infrastructure/DjangoFramework/persistence
```

---

## 📊 Cobertura Objetivo

**Meta realista para proyecto personal:**
- 🎯 **30-40% cobertura total** (suficiente)
- 🎯 **80%+ en funciones críticas** (permisos, portadas, propuestas)

**NO te obsesiones con 100%.** Es un proyecto personal, no una startup.

---

## 🛠️ Fixtures Útiles

```python
# tests/conftest.py
import pytest
from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

@pytest.fixture
def test_user():
    """Usuario de prueba"""
    return User.objects.create(username='testuser')

@pytest.fixture
def test_world(test_user):
    """Mundo de prueba"""
    return CaosWorldORM.objects.create(
        name='Test World',
        author=test_user,
        id='test_id'
    )

@pytest.fixture
def test_admin():
    """Admin de prueba"""
    user = User.objects.create(username='admin', is_staff=True)
    # Configurar perfil admin
    return user
```

---

## 🚨 Cuándo Añadir Tests

**Añade un test cuando:**
1. ✅ Una feature se rompe por segunda vez
2. ✅ Vas a refactorizar código crítico
3. ✅ Añades lógica de permisos nueva
4. ✅ Antes de un "deploy" importante

**NO añadas tests para:**
- ❌ Código que funciona y no cambias
- ❌ Templates (prueba visual es suficiente)
- ❌ Funciones triviales (getters/setters)

---

## 📝 Checklist Antes de Añadir Feature Nueva

- [ ] ¿Esta feature afecta permisos? → Añade test
- [ ] ¿Esta feature maneja archivos/imágenes? → Añade test
- [ ] ¿Esta feature es crítica para el negocio? → Añade test
- [ ] ¿Es solo UI/cosmético? → No necesitas test

---

**Última actualización:** 2026-01-03
**Mantenido por:** IAs colaboradoras del proyecto
