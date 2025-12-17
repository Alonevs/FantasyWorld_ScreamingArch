from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect

class IsAuthorOrSuperuserMixin(UserPassesTestMixin):
    """
    Permite acceso solo si es Superusuario O si es el Autor de la entidad.
    Asume que la vista tiene `get_object()` o que podemos inferir la entidad.
    """
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
            
        if self.request.user.is_superuser:
            return True
            
        # Intentar obtener el objeto para comprobar autoría
        try:
            obj = self.get_object()
            
            # Comprobar campo 'author' (World)
            if hasattr(obj, 'author') and obj.author == self.request.user:
                return True
                
            # Comprobar campo 'created_by' (Narrative)
            if hasattr(obj, 'created_by') and obj.created_by == self.request.user:
                return True

            # Si es una Propuesta/Versión, comprobar 'author'
            if hasattr(obj, 'author') and obj.author == self.request.user:
                return True
                
        except:
            # Si no hay objeto (ej: crear), o falla, denegar (o manejar aparte)
            return False
            
        return False
        
    def handle_no_permission(self):
        # Redirigir o mostrar error
        if not self.request.user.is_authenticated:
            return redirect('login')
        # Aquí podríamos redirigir a una página de "Solicitar Edición" (Propuestas)
        # Por ahora 403 o redirect home
        return redirect('home')
