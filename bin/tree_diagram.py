#!/usr/bin/env python3
"""
Tree Diagram Generator with Emojis
Generates a file structure diagram with folder and file emojis
"""

import os
import sys
from pathlib import Path

def get_emoji(path):
    """Get appropriate emoji for file/folder"""
    if path.is_dir():
        return "📁"
    else:
        ext = path.suffix.lower()
        if ext in ['.py']:
            return "🐍"
        elif ext in ['.md']:
            return "📄"
        elif ext in ['.json']:
            return "📋"
        elif ext in ['.yml', '.yaml']:
            return "⚙️"
        elif ext in ['.sh']:
            return "🔧"
        elif ext in ['.txt']:
            return "📝"
        elif ext in ['.toml']:
            return "📦"
        elif ext in ['.safetensors', '.bin']:
            return "🤖"
        elif ext in ['.db', '.sqlite']:
            return "🗄️"
        elif ext in ['.log']:
            return "📊"
        elif ext in ['.conf', '.cfg']:
            return "⚙️"
        elif ext in ['.service']:
            return "🔧"
        elif ext in ['.gitignore']:
            return "🙈"
        elif ext in ['.dockerfile', 'Dockerfile']:
            return "🐳"
        elif ext in ['.html', '.htm']:
            return "🌐"
        elif ext in ['.css']:
            return "🎨"
        elif ext in ['.js']:
            return "📜"
        elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
            return "🖼️"
        elif ext in ['.zip', '.tar', '.gz']:
            return "📦"
        elif ext in ['.pdf']:
            return "📕"
        elif ext in ['.exe', '.app']:
            return "⚡"
        else:
            return "📄"

def should_ignore(path, ignore_patterns=None):
    """Check if path should be ignored"""
    if ignore_patterns is None:
        ignore_patterns = [
            '__pycache__', '.git', '.pytest_cache', '.mypy_cache',
            'node_modules', '.venv', 'venv', '.env', '.DS_Store',
            '*.pyc', '*.pyo', '*.pyd', '.coverage', 'htmlcov'
        ]
    
    path_str = str(path)
    for pattern in ignore_patterns:
        if pattern in path_str or path.name == pattern:
            return True
    return False

def generate_tree(root_path, prefix="", is_last=True, max_depth=10, current_depth=0):
    """Generate tree structure with emojis"""
    if current_depth >= max_depth:
        return ""
    
    root = Path(root_path)
    if not root.exists():
        return f"❌ Path does not exist: {root_path}\n"
    
    # Get emoji for current item
    emoji = get_emoji(root)
    name = root.name if root.name else str(root)
    
    # Create connector
    connector = "└── " if is_last else "├── "
    result = f"{prefix}{connector}{emoji} {name}\n"
    
    if root.is_dir():
        try:
            # Get all items, sorted (directories first, then files)
            items = []
            for item in sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                if not should_ignore(item):
                    items.append(item)
            
            # Generate tree for each item
            for i, item in enumerate(items):
                is_last_item = (i == len(items) - 1)
                new_prefix = prefix + ("    " if is_last else "│   ")
                
                result += generate_tree(
                    item, 
                    new_prefix, 
                    is_last_item, 
                    max_depth, 
                    current_depth + 1
                )
                
        except PermissionError:
            result += f"{prefix}    ❌ Permission denied\n"
        except Exception as e:
            result += f"{prefix}    ❌ Error: {e}\n"
    
    return result

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python tree_diagram.py <path> [max_depth]")
        print("Example: python tree_diagram.py . 5")
        sys.exit(1)
    
    root_path = sys.argv[1]
    max_depth = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    print(f"🌳 File Structure Diagram for: {root_path}")
    print("=" * 50)
    
    tree = generate_tree(root_path, max_depth=max_depth)
    print(tree)
    
    # Add summary
    root = Path(root_path)
    if root.exists():
        file_count = sum(1 for f in root.rglob('*') if f.is_file() and not should_ignore(f))
        dir_count = sum(1 for d in root.rglob('*') if d.is_dir() and not should_ignore(d))
        print(f"📊 Summary: {file_count} files, {dir_count} directories")

if __name__ == "__main__":
    main()
