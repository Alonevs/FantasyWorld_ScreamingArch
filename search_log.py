
import re
try:
    content = open('all_output.txt', encoding='utf-16').read()
except:
    try:
        content = open('all_output.txt', encoding='utf-8').read()
    except:
        content = open('all_output.txt').read()

lines = content.splitlines()
found = False
for i, line in enumerate(lines):
    if "Error de edición" in line:
        print(f"FOUND EXCEPTION: {line}")
        # Print next few lines
        for j in range(1, 10):
            if i + j < len(lines): print(lines[i+j])
        found = True

if not found:
    print("No 'Error de edición' found. Checking for other errors...")
    for i, line in enumerate(lines):
        if "Traceback" in line:
            print(line)
            for j in range(1, 10):
                if i + j < len(lines): print(lines[i+j])
            break
