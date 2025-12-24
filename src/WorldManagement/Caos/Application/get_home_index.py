class GetHomeIndexUseCase:
    """
    Encapsula la lógica de filtrado e indexación para las entidades de la Página de Inicio (Home).
    Su objetivo es ofrecer una vista limpia y jerárquica aplicando dos reglas fundamentales:
    
    1. Limpieza de Versiones/Fantasmas: Ocultar duplicados estructurales, permitiendo 
       excepciones para niveles profundos (Geografía) donde el '00' puede ser parte del ID real.
    2. Indexación Agresiva: Seleccionar un único representante "primogénito" (generalmente el 01)
       por cada rama/tabla para simplificar la navegación en listas largas.
    """

    def execute(self, all_entities):
        """
        Procesa el listado raw de entidades y devuelve una lista optimizada para el índice.
        
        Args:
            all_entities (list/QuerySet): Lista bruta de entidades visibles (ya filtradas por permisos).
        """
        
        # 1. AGRUPACIÓN POR TRONCO (Detección de duplicados jerárquicos)
        # El objetivo es identificar qué entidades pertenecen al mismo "cuerpo" lógico.
        winners_by_trunk = {}
        for m in all_entities:
            trunk_id = m.id
            if '00' in m.id:
                level = len(m.id) // 2
                # REGLA: A partir del Nivel 7 (Geografía), no colapsamos por '00' para evitar
                # ocultar entidades válidas que usan relleno jerárquico.
                if level >= 7:
                    trunk_id = m.id
                else:
                    # En niveles de Cosmología (L1-L6), colapsamos el fragmento '00'
                    # para tratarlo como una sub-versión o puente estructural.
                    trunk_id = m.id.split('00')[0]
                
            if trunk_id not in winners_by_trunk:
                winners_by_trunk[trunk_id] = []
            winners_by_trunk[trunk_id].append(m)
        
        pre_list = []
        for pid, candidates in winners_by_trunk.items():
            # Orden de prioridad: Identificadores limpios (sin 00) > Longitud > Orden alfabético
            candidates.sort(key=lambda x: ('00' in x.id, len(x.id), x.id))
            winner = candidates[0]
            
            # FILTRO DE SEGURIDAD PARA FANTASMAS ESTRUCTURALES:
            # Si el ganador es un fragmento '00' en niveles bajos (Cosmología) y no es
            # la raíz misma del tronco, lo ocultamos para evitar ver "piezas sueltas".
            is_ghost_structure = ('00' in winner.id and (len(winner.id)//2) < 7)
            if is_ghost_structure and winner.id != pid:
                continue
                
            pre_list.append(winner)

        # 2. LÓGICA DE INDEXACIÓN AGRESIVA: Un representante por Rama (Preferencia al 01)
        # Esto cumple la regla de "mostrar solo el primer hijo de cada tabla" para navegación rápida.
        # Aplicable a Geografía (L7-L11) y Población/Personajes (L12+) según requerimientos.
        
        indexed_groups = {}
        for m in pre_list:
            # Ocultamos puentes puros (puentes '00' que no contienen datos reales)
            if m.id.endswith('00'):
                continue

            # Agrupamos por Padre y Nivel
            parent_id = m.id[:-2]
            level = len(m.id)
            group_key = (parent_id, level)
            if group_key not in indexed_groups:
                indexed_groups[group_key] = []
            indexed_groups[group_key].append(m)
            
        final_list = []
        for key, candidates in indexed_groups.items():
            # Ordenamos por ID para asegurar que el 01 sea el representante (primogénito)
            candidates.sort(key=lambda x: x.id)
            final_list.append(candidates[0])

        # Ordenación final por J-ID para mantener la coherencia visual en pantalla
        final_list.sort(key=lambda x: x.id)
        
        return final_list
