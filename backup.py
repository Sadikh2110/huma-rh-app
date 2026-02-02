import shutil
import os
from datetime import datetime

def backup_database():
    db_path = "instance/huma_rh.db"  # Ajustez le chemin
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{backup_dir}/huma_rh_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup créé : {backup_path}")