from src.Infrastructure.DjangoFramework.persistence.models import CaosNarrativeORM, CaosWorldORM

class UpdateNarrativeUseCase:
    def execute(self, nid: str, titulo: str, contenido: str, narrador: str, tipo: str, menciones_ids: list = None):
        try:
            narrativa = CaosNarrativeORM.objects.get(nid=nid)
            narrativa.titulo = titulo
            narrativa.contenido = contenido
            narrativa.narrador = narrador
            narrativa.tipo = tipo
            
            # Actualizar menciones si se envían
            if menciones_ids is not None:
                entidades = CaosWorldORM.objects.filter(id__in=menciones_ids)
                narrativa.menciones.set(entidades)
                
            narrativa.save()
            print(f" ✒️ Narrativa {nid} actualizada (Tipo: {tipo}).")
        except CaosNarrativeORM.DoesNotExist:
            raise Exception("Narrativa no encontrada.")
