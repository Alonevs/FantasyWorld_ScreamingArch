
import os

file_path = r"c:\Users\xico0\Desktop\FantasyWorld_ScreamingArch\src\Infrastructure\DjangoFramework\persistence\templates\staff\user_detail.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# I need to replace the entire REVIEWS CONTAINER block I added in the previous script.
# It starts with <!-- REVIEWS CONTAINER -->
# Ends with the closing div of "flex-col gap-4" which is the parent.

start_marker = '<!-- REVIEWS CONTAINER -->'
if start_marker not in content:
    # Try the one before that step? No, step 11 succeeded.
    # Let me check the file content first? 
    # Actually, the file content might have slightly different whitespace or quote types if I pasted it manually.
    pass

# Let's find the start marker
idx_start = content.find(start_marker)
if idx_start == -1:
    print("Error: Could not find Reviews Container.")
    exit(1)

# The block ends before the closing </div> of the parent container.
# The parent container starts at '<div class="flex flex-col gap-4">'
# The structure is:
# <div class="flex flex-col gap-4">
#    <a href="{% url 'social_hub' %}...</a>
#    <!-- REVIEWS CONTAINER -->
#    <div class="w-full ..."> ... </div>
# </div>

# So I want to replace everything from <!-- REVIEWS CONTAINER --> up to the second-to-last </div>?
# Let's target the exact div structure.

idx_div_start = content.find('<div class="w-full rounded-2xl', idx_start)
# Find the matching closing div for this one.
# It's a big block.
# Easier strategy: Find the start (<!-- REVIEWS CONTAINER -->) and find '</div>' of the parent?
# No, let's find the end of the previous anchor tag, and text "Interacciones Sociales".

anchor_end_marker = 'Interacciones Sociales</span>\n                        </div>\n                    </a>'
# This is risky due to whitespace.

# Let's rely on the start marker '<!-- REVIEWS CONTAINER -->' 
# And the fact that it is followed by the div, and then the parent closing div.
# I want to REPLACE the block with the NEW LINK.

new_html_content = """                    <!-- RANKING LINK (Replaces embedded reviews) -->
                    <a href="{% url 'user_ranking' target_user.id %}" class="w-full rounded-2xl bg-black/40 border border-white/5 p-6 flex items-center justify-center text-gray-600 hover:border-yellow-500/30 transition cursor-pointer hover:bg-white/5 group">
                        <div class="text-center group-hover:scale-105 transition-transform">
                            <span class="block text-2xl mb-1 group-hover:text-yellow-400 transition-colors">🏆</span>
                            <span class="text-[10px] uppercase font-black tracking-widest group-hover:text-white transition-colors">Ranking & Likes</span>
                            <div class="mt-2 text-[9px] text-gray-700 font-bold uppercase tracking-widest group-hover:text-yellow-500/70">
                                Ver Top Contenido
                            </div>
                        </div>
                    </a>"""

# find start
idx_start = content.find(start_marker)
# find end of the div. 
# Robust way: Count open/close divs starting from idx_div_start
idx_div_start = content.find('<div', idx_start)

# Python 101: Balance parenthesis
balance = 0
idx = idx_div_start
found_start = False
end_idx = -1

while idx < len(content):
    if content[idx:idx+4] == '<div':
        balance += 1
        found_start = True
    elif content[idx:idx+5] == '</div':
        balance -= 1
        if found_start and balance == 0:
            end_idx = idx + 6
            break
    idx += 1

if end_idx != -1:
    final = content[:idx_start] + new_html_content + content[end_idx:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final)
    print("Successfully replaced reviews with link.")
else:
    print("Could not balance divs.")
