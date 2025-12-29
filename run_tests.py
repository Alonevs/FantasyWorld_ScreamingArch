import subprocess
import sys

result = subprocess.run(
    [sys.executable, 'manage.py', 'test', 'persistence.tests.test_period_workflow', '-v', '2'],
    capture_output=True,
    text=True,
    cwd=r'c:\Users\xico0\Desktop\FantasyWorld_ScreamingArch\src\Infrastructure\DjangoFramework'
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nExit Code: {result.returncode}")

# Extract summary
lines = result.stderr.split('\n')
for i, line in enumerate(lines):
    if 'Ran' in line or 'OK' in line or 'FAILED' in line or 'ERROR' in line:
        print(line)
