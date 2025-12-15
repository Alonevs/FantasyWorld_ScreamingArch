
import nanoid
import re

# --- NanoID Logic (Public IDs) ---
def generate_nanoid(size=10):
    """Generates a URL-safe, obscure ID (NanoID)."""
    return nanoid.generate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz-', size)

def is_valid_nanoid(pid):
    """Checks if a string looks like a standard NanoID."""
    if not pid: return False
    return len(pid) == 10 and bool(re.match(r'^[A-Za-z0-9_-]+$', pid))

# --- J-ID Logic (Internal Hierarchy) ---
def get_level_u(jid):
    """Calculates hierarchy level from J-ID length (2 chars = 1 level)."""
    if not jid: return 0
    return len(jid) // 2

def get_parent_jid(jid):
    """Returns the parent J-ID (removes last 2 chars)."""
    if not jid or len(jid) <= 2: return None
    return jid[:-2]

def get_next_child_jid(parent_jid, existing_children_ids):
    """
    Calculates the next available child ID (sequential hex: 01, 02.. 09, 0A.. FF).
    This logic mimics the old repo behavior but centralized here.
    """
    if not existing_children_ids:
        # First child
        return f"{parent_jid}01"
        
    # Sort and take last
    existing_children_ids = sorted(existing_children_ids)
    last_id = existing_children_ids[-1]
    
    # Extract last segment
    last_segment = last_id[-2:]
    try:
        val = int(last_segment, 16)
        next_val = val + 1
        return f"{parent_jid}{next_val:02X}"
    except ValueError:
        # Fallback if not hex
        return f"{parent_jid}01"
