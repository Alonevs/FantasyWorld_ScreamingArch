
try:
    content = open('last_run.txt', encoding='utf-16').read()
except:
    try:
        content = open('last_run.txt', encoding='utf-8').read()
    except:
        content = open('last_run.txt').read()

print("--- START EXTRACT ---")
if "Traceback" in content:
    parts = content.split("Traceback")
    # Print the first traceback found
    print("Traceback" + parts[1][:1000]) 
else:
    print(content[:2000])
print("--- END EXTRACT ---")
