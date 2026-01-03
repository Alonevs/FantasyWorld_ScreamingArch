
import os

file_path = r"c:\Users\xico0\Desktop\FantasyWorld_ScreamingArch\src\Infrastructure\DjangoFramework\persistence\templates\staff\user_detail.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# The target block to replace (simplified search to avoid whitespace issues)
start_marker = '<div class="flex flex-col sm:flex-row gap-4">'
end_marker = '</div>'

# We find the specific occurrence near the end of the file (stats section)
# It's inside the Professional Bio column, so it's likely the last occurrence of this specific class combo?
# Let's search for the unique "social_hub" link inside it to be sure.

target_fingerprint = '{% url \'social_hub\' %}'

if target_fingerprint not in content:
    print("Error: Could not find social hub link.")
    exit(1)

# Construct the NEW content
new_html = """                <div class="flex flex-col gap-4">
                    <!-- Social Hub Link -->
                    <a href="{% url 'social_hub' %}" class="w-full p-6 rounded-2xl bg-black/40 border border-white/5 flex items-center justify-center text-gray-600 hover:border-white/20 transition cursor-pointer hover:bg-white/5 group">
                        <div class="text-center group-hover:scale-105 transition-transform">
                            <span class="block text-2xl mb-1 group-hover:text-blue-400 transition-colors">🌍</span>
                            <span class="text-[10px] uppercase font-black tracking-widest group-hover:text-white transition-colors">{{ comments_received|default:0 }} Interacciones Sociales</span>
                        </div>
                    </a>

                    <!-- REVIEWS CONTAINER -->
                    <div class="w-full rounded-2xl bg-black/40 border border-white/5 p-6" x-data="{ reviewTab: 'images', expanded: false }">
                        <!-- Card Header / Toggle -->
                        <div @click="expanded = !expanded" class="cursor-pointer text-center group">
                            <div class="text-center transition-transform duration-300" :class="expanded ? 'scale-105' : ''">
                                <span class="block text-2xl mb-1 group-hover:scale-110 transition-transform">⭐</span>
                                <span class="text-[10px] uppercase font-black tracking-widest text-gray-600 group-hover:text-yellow-500 transition-colors">{{ favorite_reviews|default:0 }} Reseñas Totales</span>
                            </div>
                            <div class="mt-2 text-[9px] text-gray-700 font-bold uppercase tracking-widest animate-pulse group-hover:text-gray-500">
                                <span x-show="!expanded">▼ Ver Detalles</span>
                                <span x-show="expanded">▲ Ocultar</span>
                            </div>
                        </div>

                        <!-- Content Area (Expandable) -->
                        <div x-show="expanded" x-collapse class="mt-8 border-t border-white/5 pt-6">
                             
                            <!-- Avg Rating Badge -->
                            {% if avg_rating > 0 %}
                            <div class="flex justify-center mb-6">
                                <div class="px-4 py-1 bg-yellow-500/10 border border-yellow-500/20 rounded-full flex items-center gap-2">
                                     <span class="text-yellow-400 font-black text-lg">{{ avg_rating }}</span>
                                     <span class="text-[10px] text-yellow-500/70 font-bold uppercase tracking-widest">/ 5.0 Promedio</span>
                                </div>
                            </div>
                            {% endif %}

                            <!-- Tabs -->
                             <div class="flex justify-center gap-2 mb-6">
                                <button @click="reviewTab = 'narratives'" 
                                    :class="reviewTab === 'narratives' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'"
                                    class="px-4 py-2 rounded-xl text-[10px] font-black tracking-widest uppercase transition-all flex items-center gap-2">
                                    <span>📜</span> Crónicas
                                </button>
                                <button @click="reviewTab = 'images'" 
                                     :class="reviewTab === 'images' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'"
                                    class="px-4 py-2 rounded-xl text-[10px] font-black tracking-widest uppercase transition-all flex items-center gap-2">
                                    <span>🖼️</span> Imágenes
                                </button>
                            </div>

                            <!-- Lists -->
                            <div x-show="reviewTab === 'images'" class="space-y-3">
                                {% for review in reviews_images %}
                                <div class="bg-black/20 border border-white/5 rounded-xl p-3 flex gap-3 hover:border-blue-500/30 transition-colors">
                                     <div class="w-10 h-10 rounded-lg overflow-hidden shrink-0 border border-white/10">
                                         <img src="{{ review.thumbnail }}" class="w-full h-full object-cover">
                                     </div>
                                     <div class="flex-1 min-w-0">
                                         <div class="flex justify-between items-baseline mb-1">
                                             <a href="{{ review.link }}" class="text-blue-400 font-bold text-xs hover:underline truncate">{{ review.entity_name }}</a>
                                             <div class="flex text-yellow-500 text-[8px]">
                                                 {% for i in review.rating_range %}⭐{% endfor %}
                                             </div>
                                         </div>
                                         <p class="text-gray-400 text-[10px] italic line-clamp-2">"{{ review.content }}"</p>
                                     </div>
                                </div>
                                {% empty %}
                                <div class="text-center text-gray-700 text-[10px] italic py-4">Sin reseñas.</div>
                                {% endfor %}
                            </div>

                            <div x-show="reviewTab === 'narratives'" class="space-y-3" style="display:none;">
                                {% for review in reviews_narratives %}
                                <div class="bg-black/20 border border-white/5 rounded-xl p-3 hover:border-purple-500/30 transition-colors">
                                     <div class="flex justify-between items-baseline mb-1">
                                         <span class="text-purple-400 font-bold text-xs truncate">{{ review.entity_name }}</span>
                                         <div class="flex text-yellow-500 text-[8px]">{% for i in review.rating_range %}⭐{% endfor %}</div>
                                     </div>
                                     <p class="text-gray-400 text-[10px] italic line-clamp-2">"{{ review.content }}"</p>
                                </div>
                                {% empty %}
                                <div class="text-center text-gray-700 text-[10px] italic py-4">Sin reseñas.</div>
                                {% endfor %}
                            </div>

                        </div>
                    </div>
                </div>"""

# Find start index
idx_start = content.find(start_marker)
if idx_start == -1:
    print("Error: Could not find start marker.")
    exit(1)

# Find ending div (It's the closing div of the 'flex-col sm:flex-row' block)
# We can find the closing div by counting braces or finding the end of the known block
# The known block ends with the second stats card div closing, then the parent div closing.
# Let's verify by finding the stats text
idx_end_text = content.find('Reseñas Totales', idx_start)
idx_end_div = content.find('</div>', idx_end_text) # Close inner div
idx_end_div = content.find('</div>', idx_end_div + 1) # Close flex-1 div
idx_end_block = content.find('</div>', idx_end_div + 1) # Close parent div

if idx_end_block == -1:
    print("Error: Could not find end of block.")
    exit(1)

final_content = content[:idx_start] + new_html + content[idx_end_block+6:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(final_content)

print("Successfully updated user_detail.html")
