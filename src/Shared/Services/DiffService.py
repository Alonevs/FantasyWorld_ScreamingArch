
class DiffService:
    @staticmethod
    def compare_entity(entity, proposed_data):
        """
        Compares an entity vs a proposed JSON payload.
        Returns a list of diff objects: { 'field': 'Title', 'old': '...', 'new': '...' }
        """
        diffs = []
        
        # 1. Compare Name/Title
        if 'titulo' in proposed_data and proposed_data['titulo'] != entity.name:
            diffs.append({
                'field': 'Nombre',
                'old': entity.name,
                'new': proposed_data['titulo']
            })
            
        # 2. Compare Description (Plain Text comparison for simplicity)
        if 'descripcion' in proposed_data:
            # Normalize newlines
            new_desc = proposed_data['descripcion'].replace('\r\n', '\n').strip()
            old_desc = (entity.description or "").replace('\r\n', '\n').strip()
            
            if new_desc != old_desc:
                diffs.append({
                    'field': 'Descripción',
                    'old': old_desc,
                    'new': new_desc,
                    'is_long': True
                })
        
        # 3. Compare Metadata/Tags (if any)
        if 'metadata' in proposed_data:
            old_meta = entity.metadata or {}
            new_meta = proposed_data['metadata'] or {}
            meta_diffs = DiffService.compare_metadata(old_meta, new_meta)
            diffs.extend(meta_diffs)
        
        return diffs
    
    @staticmethod
    def compare_metadata(old_meta: dict, new_meta: dict) -> list:
        """
        Compara dos diccionarios de metadata y retorna diferencias.
        
        Args:
            old_meta: Metadata actual de la entidad
            new_meta: Metadata propuesta
            
        Returns:
            Lista de diferencias en formato estándar
        """
        diffs = []
        all_keys = set(old_meta.keys()) | set(new_meta.keys())
        
        for key in sorted(all_keys):
            old_val = old_meta.get(key)
            new_val = new_meta.get(key)
            
            # Skip if values are identical
            if old_val == new_val:
                continue
            
            # Handle nested dictionaries
            if isinstance(old_val, dict) and isinstance(new_val, dict):
                nested_diffs = DiffService.compare_metadata(old_val, new_val)
                for nested_diff in nested_diffs:
                    nested_diff['field'] = f"{key}.{nested_diff['field']}"
                diffs.extend(nested_diffs)
            else:
                diffs.append({
                    'field': f'Metadata: {key}',
                    'old': str(old_val) if old_val is not None else '-',
                    'new': str(new_val) if new_val is not None else '-'
                })
        
        return diffs

    @staticmethod
    def get_create_preview(proposed_data):
        """
        Returns a structured preview of what will be created.
        """
        return [
            {'field': 'Nombre', 'value': proposed_data.get('titulo', '-')},
            {'field': 'Descripción', 'value': proposed_data.get('descripcion', '-'), 'is_long': True},
            {'field': 'Tipo', 'value': proposed_data.get('tipo', 'Desconocido')},
        ]
