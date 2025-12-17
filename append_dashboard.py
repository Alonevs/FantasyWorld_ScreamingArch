
src = r"c:\Users\xico0\Desktop\FantasyWorld_ScreamingArch\src\Infrastructure\DjangoFramework\persistence\views\dashboard_fragments.py"
dest = r"c:\Users\xico0\Desktop\FantasyWorld_ScreamingArch\src\Infrastructure\DjangoFramework\persistence\views\dashboard_views.py"

with open(src, "r", encoding="utf-8") as f:
    content = f.read()

with open(dest, "a", encoding="utf-8") as f:
    f.write("\n")
    f.write(content)

print("Appended successfully.")
