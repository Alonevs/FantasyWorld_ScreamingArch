
import re

try:
    content = open('error.log', encoding='utf-16').read()
except:
    try:
        content = open('error.log', encoding='utf-8').read()
    except:
        content = open('error.log').read()

lines = content.splitlines()
for i, line in enumerate(lines):
    if "Error" in line or "Traceback" in line or "File" in line or "Exception" in line:
        print(line)
        # Print next 2 lines for context
        if i + 1 < len(lines): print(lines[i+1])
        if i + 2 < len(lines): print(lines[i+2])
