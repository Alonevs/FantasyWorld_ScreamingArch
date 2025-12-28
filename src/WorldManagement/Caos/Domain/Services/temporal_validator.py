
class TemporalConsistencyError(Exception):
    pass

class TemporalValidator:
    """
    Servicio de Dominio para validar la consistencia temporal entre entidades.
    Regla de Oro: Un hijo no puede existir antes que su padre.
    Regla de Plata: Un hijo no puede existir después de que su padre haya dejado de existir.
    """
    
    def validate_consistency(self, child_entity, parent_entity):
        """
        Verifica que las fechas del hijo estén contenidas dentro del rango del padre.
        Lanza TemporalConsistencyError si hay violación.
        Acepta entidades (con atributo .metadata) o diccionarios directos de metadatos.
        """
        if not child_entity or not parent_entity:
            return

        # Helper para extraer metadata ya sea de objeto o dict
        def get_meta(obj):
            if isinstance(obj, dict): return obj
            return getattr(obj, 'metadata', {})
            
        def get_name(obj):
            if isinstance(obj, dict): return obj.get('name', 'Entidad')
            return getattr(obj, 'name', 'Entidad')

        child_chrono = get_meta(child_entity).get('chronology', {})
        parent_chrono = get_meta(parent_entity).get('chronology', {})

        # Si no hay datos de cronología, asumimos validez (o ignoramos)
        if not child_chrono or not parent_chrono:
            return

        c_start = child_chrono.get('start_year')
        p_start = parent_chrono.get('start_year')
        c_end = child_chrono.get('end_year')
        p_end = parent_chrono.get('end_year')

        # Normalización de datos (asegurar enteros)
        try:
            c_start = int(c_start) if c_start is not None else None
            p_start = int(p_start) if p_start is not None else None
            c_end = int(c_end) if c_end is not None else None
            p_end = int(p_end) if p_end is not None else None
        except ValueError:
            return 

        # REGLA 1: Principio de Causalidad (Inicio)
        if c_start is not None and p_start is not None:
            if c_start < p_start:
                raise TemporalConsistencyError(
                    f"Paradoja Temporal: La entidad '{get_name(child_entity)}' (Año {c_start}) "
                    f"no puede nacer antes que su padre '{get_name(parent_entity)}' (Año {p_start})."
                )

        # REGLA 2: Principio de Existencia (Fin)
        if c_start is not None and p_end is not None:
             if c_start > p_end:
                raise TemporalConsistencyError(
                    f"Paradoja Temporal: La entidad '{get_name(child_entity)}' (Año {c_start}) "
                    f"nace después del fin de su padre '{get_name(parent_entity)}' (Año {p_end})."
                )
        
        # REGLA 3: Contención de Vida (Fin-Fin)
        if c_end is not None and p_end is not None:
            if c_end > p_end:
                 raise TemporalConsistencyError(
                    f"Paradoja Temporal: La entidad '{get_name(child_entity)}' termina en {c_end}, "
                    f"posterior al fin de su contenedor '{get_name(parent_entity)}' ({p_end})."
                )
            
        # REGLA 4: Coherencia Interna
        if c_start is not None and c_end is not None:
            if c_start > c_end:
                raise TemporalConsistencyError(
                    f"Incoherencia Temporal: '{get_name(child_entity)}' nace en {c_start} pero muere antes, en {c_end}."
                )
