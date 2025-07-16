"""
Fix relative imports in all Python files
Converts relative imports to absolute imports so everything works
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix relative imports in a single file"""
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace relative imports with absolute imports
    replacements = [
        # Core imports
        (r'from \.\.core\.models import', 'from core.models import'),
        (r'from \.\.core\.exceptions import', 'from core.exceptions import'),
        (r'from \.\.core\.constants import', 'from core.constants import'),
        
        # Config imports
        (r'from \.\.config\.settings import', 'from config.settings import'),
        
        # Agent imports
        (r'from \.base_agent import', 'from agents.base_agent import'),
        (r'from \.prompts import', 'from agents.prompts import'),
        
        # MCP imports
        (r'from \.base_connector import', 'from mcp.base_connector import'),
        (r'from \.google_places import', 'from mcp.google_places import'),
        (r'from \.google_weather import', 'from mcp.google_weather import'),
        
        # Graph imports
        (r'from \.state import', 'from graph.state import'),
        (r'from \.nodes import', 'from graph.nodes import'),
        (r'from \.workflow import', 'from graph.workflow import'),
        
        # Utils imports
        (r'from \.\.utils\.logger import', 'from utils.logger import'),
        (r'from \.\.utils\.formatters import', 'from utils.formatters import'),
        
        # MCP manager import
        (r'from \.\.mcp import', 'from mcp import'),
    ]
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Check if file was modified
    if content != original_content:
        # Write the fixed content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def fix_all_imports():
    """Fix imports in all Python files"""
    
    src_dir = Path("src")
    
    if not src_dir.exists():
        print("❌ src directory not found. Make sure you're in the project root.")
        return
    
    print("🔧 Fixing relative imports in all Python files...")
    
    # Find all Python files
    python_files = list(src_dir.glob("**/*.py"))
    
    fixed_count = 0
    
    for file_path in python_files:
        if file_path.name == "__init__.py":
            continue  # Skip __init__.py files
        
        try:
            if fix_imports_in_file(file_path):
                print(f"   ✅ Fixed: {file_path}")
                fixed_count += 1
            else:
                print(f"   ⚪ No changes: {file_path}")
        except Exception as e:
            print(f"   ❌ Error fixing {file_path}: {e}")
    
    print(f"\n🎉 Import fixing complete!")
    print(f"   Fixed {fixed_count} files")
    print(f"   Total files checked: {len(python_files)}")
    
    return fixed_count > 0

if __name__ == "__main__":
    print("🔧 Python Import Fixer")
    print("=" * 30)
    
    success = fix_all_imports()
    
    if success:
        print("\n🚀 Now try running your system:")
        print("   python run_full_system.py")
        print("   or")
        print("   python src/main.py")
    else:
        print("\n⚠️ No imports needed fixing. If you still have issues:")
        print("   1. Make sure you're in the project root directory")
        print("   2. Try: python -m src.main")
        print("   3. Check that all files exist")