import zipfile
import os
from pathlib import Path

def export_ai_hub():
    """
    Packages the AI Hub module and its dependencies into a zip file.
    """
    # Configuration
    # Assumes the script is run from the project root (DataVue-App)
    source_root = Path("backend")
    output_filename = "ai_hub_package.zip"
    
    # Mapping of source path (relative to backend) -> target path (inside zip)
    # We want the zip structure to look like a clean project root:
    #   ai_service.py
    #   modules/ai_hub/...
    #   services/ai/...
    
    paths_to_export = [
        "modules/ai_hub",
        "services/ai",
        "ai_service.py"
    ]

    print(f"🔄 Starting export of AI Hub to {output_filename}...")
    
    if not source_root.exists():
        print(f"❌ Error: 'backend' directory not found. Please run this script from the project root.")
        return

    files_added = 0
    
    try:
        with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item in paths_to_export:
                source_path = source_root / item
                
                if not source_path.exists():
                    print(f"⚠️ Warning: Path not found: {source_path}")
                    continue

                if source_path.is_file():
                    # Preserve filename in key root
                    # e.g. backend/ai_service.py -> ai_service.py
                    arcname = item 
                    print(f"  + Adding file: {item}")
                    zipf.write(source_path, arcname)
                    files_added += 1
                
                elif source_path.is_dir():
                    # Walk directory
                    print(f"  + Adding directory: {item}/")
                    for file_path in source_path.rglob('*'):
                        # Skip pycache and typical ignored files
                        if '__pycache__' in file_path.parts or file_path.name.startswith('.'):
                            continue
                            
                        if file_path.is_file():
                            # Calculate arcname relative to backend
                            # e.g. backend/modules/ai_hub/init.py -> modules/ai_hub/init.py
                            arcname = file_path.relative_to(source_root)
                            zipf.write(file_path, arcname)
                            files_added += 1
        
        print(f"\n✅ Success! Package created: {os.path.abspath(output_filename)}")
        print(f"📦 Total files: {files_added}")
        print("\n[如何使用]")
        print("1. 將 ai_hub_package.zip 複製到你的新專案根目錄")
        print("2. 解壓縮 (Unzip Here)")
        print("3. 安裝依賴: pip install google-genai openai")
        
    except Exception as e:
        print(f"\n❌ Error creating zip file: {e}")

if __name__ == "__main__":
    export_ai_hub()
