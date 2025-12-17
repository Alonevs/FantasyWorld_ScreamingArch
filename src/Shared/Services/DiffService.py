
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
        # TODO: Implement deep diff for JSON metadata if needed
        
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
