import os
import django
import sys
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.Infrastructure.DjangoFramework.config.settings')
django.setup()

from django.contrib.auth.models import User
from src.Infrastructure.DjangoFramework.persistence.models import CaosVersionORM, CaosNarrativeVersionORM

print("--- USERS ---")
for u in User.objects.all():
    print(f"ID: {u.id} | Username: {u.username} | Superuser: {u.is_superuser}")

print("\n--- APPROVED WORLDS ---")
ws = CaosVersionORM.objects.filter(status='APPROVED')
for w in ws:
    author = w.author.username if w.author else "None"
    print(f"ID: {w.id} | Name: {w.proposed_name} | Author: {author} | Status: {w.status}")

print("\n--- APPROVED NARRATIVES ---")
ns = CaosNarrativeVersionORM.objects.filter(status='APPROVED')
for n in ns:
    author = n.author.username if n.author else "None"
    print(f"ID: {n.id} | Title: {n.proposed_title} | Author: {author} | Status: {n.status}")

print("\n--- PENDING WORLDS ---")
ws_p = CaosVersionORM.objects.filter(status='PENDING')
for w in ws_p:
    author = w.author.username if w.author else "None"
    print(f"ID: {w.id} | Name: {w.proposed_name} | Author: {author}")
