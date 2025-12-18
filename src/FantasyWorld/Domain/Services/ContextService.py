from src.Infrastructure.DjangoFramework.persistence.models import CaosWorldORM

class ContextBuilder:
    """
    Servicio de Dominio encargado de construir el 'Contexto Situacional' 
    para la IA, recorriendo la jerarquía de entidades (Hijo -> Padre -> Abuelo).
    """

    @staticmethod
    def build_hierarchy_context(entity_id: str) -> str:
        """
        Construye un prompt de sistema con la información acumulada de la jerarquía.
        
        Args:
            entity_id (str): Puede ser el ID (PK), PublicID (NanoID) o id_codificado.
            
        Returns:
            str: Texto formateado con el contexto jerárquico.
        """
        # 1. Resolver Entidad Inicial
        current_entity = ContextBuilder._resolve_entity(entity_id)
        if not current_entity:
            return ""

        hierarchy = []
        
        # 2. Recorrer hacia arriba (usando id)
        # Asumimos que ID es jerárquico (ej: "0102" -> padre "01")
        if current_entity.id:
            # Añadir actual
            hierarchy.append(current_entity)
            
            current_code = current_entity.id
            while len(current_code) > 2: # Asumiendo chunks de 2 chars o al menos que raíz es algo
                # Cortar los últimos caracteres para obtener padre
                # Estrategia: Si es "0102", padre es "01". Si es "010205", padre "0102".
                # Asumimos bloques de 2 digitos por nivel.
                parent_code = current_code[:-2] 
                
                parent = CaosWorldORM.objects.filter(id=parent_code).first()
                if parent:
                    hierarchy.append(parent)
                    current_code = parent_code
                else:
                    break
        else:
            # Fallback: Solo la entidad actual
            hierarchy.append(current_entity)

        # 3. Construir Texto (Desde Raíz a Hijo)
        context_parts = []
        # Invertimos para ir de Padre -> Hijo
        for level, entity in enumerate(reversed(hierarchy)):
            metadata_summary = ContextBuilder._extract_relevant_metadata(entity)
            if metadata_summary:
                header = f"CONTEXTO NIVEL {level} ({entity.name}):"
                context_parts.append(f"{header}\n{metadata_summary}")

        if not context_parts:
            return ""

        return "\n___\nINFORMACIÓN DE JERARQUÍA (PARA CONCIENCIA SITUACIONAL):\n" + "\n\n".join(context_parts) + "\n___\n"

    @staticmethod
    def _resolve_entity(raw_id):
        # Misma lógica de resolución "cascada" que en ai_views
        criteria = [
            {'id': raw_id},
            {'public_id': raw_id}
        ]
        
        for criterion in criteria:
            try:
                return CaosWorldORM.objects.get(**criterion)
            except CaosWorldORM.DoesNotExist:
                continue
        return None

    @staticmethod
    def _extract_relevant_metadata(entity) -> str:
        """
        Extrae y formatea propiedades clave de la entidad.
        """
        props = entity.metadata.get('properties', [])
        if not props:
            # Fallback a descripción si no hay metadatos estructurados
            if entity.description:
                return f"Resumen: {entity.description[:200]}..."
            return ""

        # Claves de "Alta Prioridad" para contexto
        priority_keys = ['fisica', 'magia', 'tecnologia', 'sociedad', 'reglas', 'atmosfera', 'constantes', 'estructura', 'limites']
        
        lines = []
        for p in props:
            k = p.get('key', '').lower()
            v = p.get('value', '')
            
            # Incluir si coincide con prioridad o si la lista es corta (<5 props)
            is_priority = any(pk in k for pk in priority_keys)
            if is_priority or len(props) < 5:
                lines.append(f"- {p.get('key')}: {v}")
        
        return "\n".join(lines)
