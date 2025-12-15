
from src.Infrastructure.DjangoFramework.persistence.models import CaosEventLog, CaosVersionORM

def search_recovery():
    with open('recovery_results.txt', 'w', encoding='utf-8') as f:
        ids = ["010102", "010104"]
        f.write("--- SEARCH START ---\n")
        
        # 1. Search Logs by Target ID
        for i in ids:
            logs = CaosEventLog.objects.filter(target_id=i)
            f.write(f"ID {i} Logs: {logs.count()}\n")
            for l in logs:
                f.write(f"  [{l.timestamp}] {l.action}: {l.details}\n")

        # 2. Search Logs by Details Content
        f.write("- Searching Content -\n")
        for i in ids:
            logs = CaosEventLog.objects.filter(details__icontains=i)
            f.write(f"Content {i} Logs: {logs.count()}\n")
            for l in logs:
                 f.write(f"  [{l.timestamp}] {l.action} (Target: {l.target_id}): {l.details}\n")

        # 3. Search Versions
        f.write("- Searching Versions -\n")
        for i in ids:
            vs = CaosVersionORM.objects.filter(world_id=i)
            f.write(f"ID {i} Versions: {vs.count()}\n")
            for v in vs:
                 f.write(f"  V{v.version_number}: {v.proposed_name} - {v.proposed_description[:50]}...\n")
                 
        f.write("--- SEARCH END ---\n")

if __name__ == "__main__":
    search_recovery()
