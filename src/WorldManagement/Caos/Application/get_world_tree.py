from typing import List, Dict, Any
from src.WorldManagement.Caos.Domain.repositories import CaosRepository
from src.WorldManagement.Caos.Application.common import resolve_world_id

class GetWorldTreeUseCase:
    """
    Caso de Uso responsable de construir la estructura jerárquica para el Mapa del Árbol.
    Gestiona la lógica de ordenación compleja, la detección de saltos jerárquicos
    y la re-vinculación de "padres adoptivos" para asegurar que los hijos compartidos
    o saltados aparezcan correctamente anidados en la vista interactiva.
    """
    def __init__(self, repository: CaosRepository):
        self.repository = repository

    def execute(self, identifier: str) -> Dict[str, Any]:
        """
        Retorna la estructura de datos del árbol para una entidad raíz.
        """
        # Resolvemos la entidad raíz (soporta NanoID y J-ID)
        root = resolve_world_id(self.repository, identifier)
        if not root:
            return None

        # Recuperar todos los descendientes recursivamente
        descendants = self.repository.find_descendants(root.id)
        
        # --- LÓGICA DE ORDENACIÓN ESTRATÉGICA ---
        # El objetivo es agrupar las entidades compartidas ('00') junto a su "Primo Primogénito" ('01').
        # Ejemplo: Queremos que 'Mi House' (010013) aparezca justo tras los hijos directos de 'Universo' (0101).
        def tree_sort_key(node):
            original = node.id.value
            segments = [original[i:i+2] for i in range(0, len(original), 2)]
            
            # Mapeamos los segmentos '00' a '01' para la comparación de orden
            remapped_segments = []
            for s in segments:
                if s == '00':
                    remapped_segments.append('01') # Proxy hacia el Primogénito
                else:
                    remapped_segments.append(s)
            
            return "".join(remapped_segments)

        descendants.sort(key=tree_sort_key)
        
        tree_data = []
        base_len = len(root.id.value)

        # Pre-calculamos un conjunto de IDs para búsquedas rápidas de ancestros existentes
        all_ids_set = {root.id.value}
        for d in descendants: all_ids_set.add(d.id.value)
        
        for node in descendants:
            node_id_str = node.id.value
            
            # --- FILTRO DE FANTASMAS ---
            # Ocultamos nodos que sean puramente estructurales (Nombre "Nexo"/"Ghost" y terminados en 00)
            name_lower = node.name.lower()
            is_ghost_name = "nexo" in name_lower or "ghost" in name_lower or "fantasma" in name_lower or node.name in ("Placeholder", "")
            is_ghost_id = node_id_str.endswith("00")
            
            if is_ghost_id and is_ghost_name:
                continue

            # FILTRO DE SEGURIDAD: Los borradores no aparecen en el Mapa del Árbol público/estándar
            status_val = node.status.value if hasattr(node.status, 'value') else str(node.status)
            if status_val == 'DRAFT':
                continue

            # Cálculo de profundidad para el indentado visual (Nivel - Nivel Raíz)
            depth = (len(node_id_str) - base_len) // 2
            
            # --- DETECCIÓN DE SALTOS/COMPARTIDOS ---
            # Si el ID contiene un segmento '00' intermedio, es una entidad que ha "saltado" niveles.
            is_jumped = False
            for i in range(0, len(node_id_str)-2, 2):
                if node_id_str[i:i+2] == '00':
                    is_jumped = True
                    break
            
            # --- RE-VINCULACIÓN DE PADRE LÓGICO (Padre Adoptivo) ---
            # Para que el árbol colapse correctamente, buscamos hacia arriba el ancestro más cercano
            # que REALMENTE exista en la base de datos, aplicando lógica de "Foster Parent".
            def get_foster_mapped(id_val):
                """Mapea segmentos '00' a '01' para buscar al hermano primogénito adoptivo."""
                segments = [id_val[i:i+2] for i in range(0, len(id_val), 2)]
                remapped = []
                for s in segments:
                    if s == '00': remapped.append('01') 
                    else: remapped.append(s)
                return "".join(remapped)

            logical_parent_id = ""
            curr_check = node_id_str[:-2] # Empezamos por el padre directo
            
            while len(curr_check) >= len(root.id.value):
                # 1. Intentamos buscar por el mapa de "Padre Adoptivo" (01)
                candidate = get_foster_mapped(curr_check) if curr_check.endswith('00') else curr_check
                
                # 2. Si el candidato existe, es nuestro vínculo para el árbol
                if candidate in all_ids_set:
                    logical_parent_id = candidate
                    break
                
                # 3. Caso especial: si el padre real '00' existe (aunque sea fantasma), lo usamos
                if candidate != curr_check and curr_check in all_ids_set:
                    logical_parent_id = curr_check
                    break
                    
                # 4. Si no, seguimos subiendo por la jerarquía
                curr_check = curr_check[:-2]

            tree_data.append({
                'name': node.name,
                'public_id': node_id_str, 
                'logical_parent_id': logical_parent_id, 
                'id_display': f"..{node_id_str[-2:]}" if len(node_id_str) > 2 else node_id_str,
                'indent_px': depth * 30,
                'is_root': node_id_str == root.id.value,
                'status': status_val,
                'visible': node.is_public,
                'is_jumped': is_jumped
            })
            
        return {'root_name': root.name, 'tree': tree_data}
