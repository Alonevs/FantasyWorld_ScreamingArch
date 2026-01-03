
try:
    with open('final_debug.txt', 'r', encoding='utf-16', errors='replace') as f:
        content = f.read()
except:
    try:
        with open('final_debug.txt', 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except:
        with open('final_debug.txt', 'r', errors='replace') as f:
            content = f.read()

lines = content.splitlines()
found_debug = False
for line in lines:
    if "DEBUG:" in line or "FAIL:" in line:
        print(line)
        found_debug = True

if not found_debug:
    print("NO DEBUG LINES FOUND. DUMPING LAST 50 LINES:")
    for line in lines[-50:]:
        print(line)
