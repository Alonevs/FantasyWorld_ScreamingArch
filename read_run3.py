
try:
    content = open('final_verify.txt', encoding='utf-16').read()
except:
    try:
        content = open('final_verify.txt', encoding='utf-8').read()
    except:
        content = open('final_verify.txt').read()

print("--- START EXTRACT ---")
if "OK" in content:
    print("SUCCESS: OK found in output")
    print(content[-500:])
elif "FAIL:" in content:
    parts = content.split("FAIL:")
    print("FAIL:" + parts[1][:1000])
elif "Traceback" in content:
    parts = content.split("Traceback")
    print("Traceback" + parts[1][:1000])
else:
    print(content[-2000:])
print("--- END EXTRACT ---")
