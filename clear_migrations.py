import os
import glob

def clear_migrations():
    # Находим все папки migrations, исключая venv
    migration_dirs = []
    for root, dirs, files in os.walk('.'):
        # Исключаем папку venv из поиска
        if 'venv' in dirs:
            dirs.remove('venv')
        if root.endswith('migrations'):
            migration_dirs.append(root)
    
    for migration_dir in migration_dirs:
        # Находим все .py файлы кроме __init__.py
        migration_files = glob.glob(os.path.join(migration_dir, '*.py'))
        
        for file_path in migration_files:
            if not file_path.endswith('__init__.py'):
                try:
                    os.remove(file_path)
                    print(f"Удален: {file_path}")
                except Exception as e:
                    print(f"Ошибка при удалении {file_path}: {e}")

if __name__ == "__main__":
    clear_migrations()
    print("Очистка миграций завершена!")
