"""
Sistema de Validación de Metadata JSONB usando JSON Schema.

Este módulo proporciona validación estructurada para los campos metadata
de las entidades, asegurando consistencia y prevención de errores.
"""

from jsonschema import validate, ValidationError, Draft7Validator
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ESQUEMAS JSON SCHEMA PARA VALIDACIÓN
# ============================================================================

# Esquema base para timeline (preparado para futuro)
TIMELINE_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^[0-9]+$": {  # Años como claves (ej: "1500", "2000")
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "metadata": {"type": "object"},
                "images": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "cover_image": {"type": ["string", "null"]}
            },
            "required": ["description", "metadata"]
        }
    }
}

# Esquema para gallery_log
GALLERY_LOG_SCHEMA = {
    "type": "object",
    "patternProperties": {
        ".*\\.(png|jpg|jpeg|webp)$": {  # Nombres de archivo de imagen
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "uploader": {"type": "string"},
                "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"}
            }
        }
    }
}

# Esquema para datos_nucleo (propiedades físicas)
DATOS_NUCLEO_SCHEMA = {
    "type": "object",
    "properties": {
        "gravedad": {"type": "string"},
        "atmosfera": {"type": "string", "enum": ["Respirable", "Toxica", "Ninguna", "Desconocida"]},
        "clima_global": {"type": "string"},
        "bioma_dominante": {"type": "string"},
        "nivel_tecnologico": {"type": "string"},
        "poblacion": {"type": ["string", "integer"]},
        "gobierno": {"type": "string"},
        "idioma_oficial": {"type": "string"}
    }
}

# Esquema para properties (propiedades flexibles)
PROPERTIES_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "key": {"type": "string", "minLength": 1},
            "value": {"type": "string"}
        },
        "required": ["key", "value"]
    }
}

# Esquema completo de metadata
METADATA_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "timeline": TIMELINE_SCHEMA,
        "current_year": {"type": ["integer", "string", "null"]},
        "year_range": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2
        },
        "gallery_log": GALLERY_LOG_SCHEMA,
        "cover_image": {"type": ["string", "null"]},
        "datos_nucleo": DATOS_NUCLEO_SCHEMA,
        "datos_extendidos": {"type": "object"},
        "properties": PROPERTIES_SCHEMA,
        "tipo_entidad": {
            "type": "string",
            "enum": [
                "CAOS", "ABISMO", "UNIVERSO", "GALAXIA", "SISTEMA", "PLANETA",
                "DIMENSION", "GEOGRAFIA", "SOCIEDAD", "CRIATURA", "OBJETO",
                "CIUDAD", "LUGAR"
            ]
        },
        "static_metadata": {"type": "object"},
        "analysis_trace": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "additionalProperties": True  # Permitir campos adicionales por flexibilidad
}


# ============================================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================================

def validate_metadata(metadata: Dict[str, Any], strict: bool = False) -> tuple[bool, Optional[str]]:
    """
    Valida un diccionario de metadata contra el esquema JSON Schema.
    
    Args:
        metadata: Diccionario de metadata a validar
        strict: Si True, no permite propiedades adicionales
        
    Returns:
        Tupla (es_valido, mensaje_error)
        
    Examples:
        >>> metadata = {"gallery_log": {"img.png": {"title": "Test"}}}
        >>> is_valid, error = validate_metadata(metadata)
        >>> print(is_valid)
        True
    """
    if not metadata:
        return True, None
    
    try:
        # Crear validador
        schema = METADATA_SCHEMA.copy()
        if strict:
            schema["additionalProperties"] = False
        
        validator = Draft7Validator(schema)
        
        # Validar
        errors = list(validator.iter_errors(metadata))
        
        if errors:
            # Formatear errores de forma legible
            error_messages = []
            for error in errors[:3]:  # Mostrar solo los primeros 3 errores
                path = ".".join(str(p) for p in error.path) if error.path else "root"
                error_messages.append(f"{path}: {error.message}")
            
            error_msg = "; ".join(error_messages)
            if len(errors) > 3:
                error_msg += f" (y {len(errors) - 3} errores más)"
            
            logger.warning(f"Metadata validation failed: {error_msg}")
            return False, error_msg
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error during metadata validation: {e}")
        return False, f"Validation error: {str(e)}"


def validate_timeline_snapshot(snapshot: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Valida un snapshot individual de timeline.
    
    Args:
        snapshot: Diccionario con datos del snapshot
        
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    schema = {
        "type": "object",
        "properties": {
            "description": {"type": "string", "minLength": 10},
            "metadata": {"type": "object"},
            "images": {"type": "array", "items": {"type": "string"}},
            "cover_image": {"type": ["string", "null"]}
        },
        "required": ["description", "metadata"]
    }
    
    try:
        validate(instance=snapshot, schema=schema)
        return True, None
    except ValidationError as e:
        return False, e.message


def validate_gallery_entry(filename: str, entry: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Valida una entrada individual de gallery_log.
    
    Args:
        filename: Nombre del archivo de imagen
        entry: Diccionario con metadata de la imagen
        
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    # Validar extensión de archivo
    valid_extensions = ['.png', '.jpg', '.jpeg', '.webp']
    if not any(filename.lower().endswith(ext) for ext in valid_extensions):
        return False, f"Invalid image extension for {filename}"
    
    # Validar estructura del entry
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "uploader": {"type": "string"},
            "date": {"type": "string"}
        }
    }
    
    try:
        validate(instance=entry, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"{filename}: {e.message}"


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Limpia y normaliza metadata antes de guardar.
    
    Args:
        metadata: Metadata a limpiar
        
    Returns:
        Metadata limpia y normalizada
    """
    if not metadata:
        return {}
    
    cleaned = metadata.copy()
    
    # Normalizar current_year a entero
    if 'current_year' in cleaned and cleaned['current_year']:
        try:
            cleaned['current_year'] = int(cleaned['current_year'])
        except (ValueError, TypeError):
            del cleaned['current_year']
    
    # Asegurar que gallery_log es un diccionario
    if 'gallery_log' in cleaned and not isinstance(cleaned['gallery_log'], dict):
        cleaned['gallery_log'] = {}
    
    # Asegurar que properties es una lista
    if 'properties' in cleaned and not isinstance(cleaned['properties'], list):
        cleaned['properties'] = []
    
    # Eliminar valores None de nivel superior
    cleaned = {k: v for k, v in cleaned.items() if v is not None}
    
    return cleaned


# ============================================================================
# DECORADOR PARA VALIDACIÓN AUTOMÁTICA
# ============================================================================

def validate_metadata_on_save(func):
    """
    Decorador para validar metadata antes de guardar un modelo.
    
    Usage:
        @validate_metadata_on_save
        def save(self, *args, **kwargs):
            super().save(*args, **kwargs)
    """
    def wrapper(instance, *args, **kwargs):
        if hasattr(instance, 'metadata') and instance.metadata:
            # Sanitizar primero
            instance.metadata = sanitize_metadata(instance.metadata)
            
            # Validar
            is_valid, error = validate_metadata(instance.metadata)
            
            if not is_valid:
                logger.warning(
                    f"Metadata validation warning for {instance.__class__.__name__} "
                    f"{getattr(instance, 'id', 'unknown')}: {error}"
                )
                # No bloqueamos el guardado, solo advertimos
                # Para modo estricto, descomentar la siguiente línea:
                # raise ValueError(f"Invalid metadata: {error}")
        
        return func(instance, *args, **kwargs)
    
    return wrapper
