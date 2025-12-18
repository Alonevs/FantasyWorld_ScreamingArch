# --- J-ID Logic (Internal Hierarchy) ---
def get_level_u(jid):
    """Calculates hierarchy level from J-ID length (2 chars = 1 level)."""
    if not jid: return 0
    return len(jid) // 2

def get_parent_jid(jid):
    """Returns the parent J-ID (removes last 2 chars)."""
    if not jid or len(jid) <= 2: return None
    return jid[:-2]
