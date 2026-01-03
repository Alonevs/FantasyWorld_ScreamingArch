"""
Tests para el proyecto FantasyWorld.

Organización:
- test_permissions.py: Tests de permisos (mundos, propuestas, equipos)
- test_cover_detection.py: Tests de detección de portadas
- test_proposals.py: Tests del sistema de propuestas ECLAI
- test_period_workflow.py: Tests del workflow de períodos

Para ejecutar todos los tests:
    python manage.py test src.Infrastructure.DjangoFramework.persistence.tests

Para ejecutar un archivo específico:
    python manage.py test src.Infrastructure.DjangoFramework.persistence.tests.test_permissions

Para ejecutar un test específico:
    python manage.py test src.Infrastructure.DjangoFramework.persistence.tests.test_permissions.WorldPermissionsTestCase.test_user_cannot_edit_others_world
"""
