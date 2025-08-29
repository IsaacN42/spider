#!/usr/bin/env python3
# spider/scripts/list_structure.py

"""
lists spider project directory structure excluding gitignore patterns
"""

import os
import fnmatch
from pathlib import Path

def load_gitignore_patterns(gitignore_path):
    # load patterns from .gitignore file
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    return patterns

def should_ignore(path, patterns):
    # check if path matches any gitignore pattern
    path_str = str(path)
    for pattern in patterns:
        # handle directory patterns
        if pattern.endswith('/'):
            if fnmatch.fnmatch(path_str + '/', '*' + pattern):
                return True
        # handle file patterns
        elif fnmatch.fnmatch(path_str, '*' + pattern):
            return True
        # handle exact matches
        elif pattern in path_str:
            return True
    return False

def list_directory_tree(root_path, gitignore_patterns, prefix="", is_last=True):
    # get directory structure with tree formatting
    root = Path(root_path)
    
    if should_ignore(root, gitignore_patterns):
        return
    
    # print current directory/file
    connector = "└── " if is_last else "├── "
    print(f"{prefix}{connector}{root.name}")
    
    if root.is_dir():
        # get all items in directory
        try:
            items = sorted([item for item in root.iterdir() 
                          if not should_ignore(item, gitignore_patterns)])
        except PermissionError:
            return
        
        # recursive print for each item
        for i, item in enumerate(items):
            is_last_item = (i == len(items) - 1)
            new_prefix = prefix + ("    " if is_last else "│   ")
            list_directory_tree(item, gitignore_patterns, new_prefix, is_last_item)

def main():
    # script entry point
    spider_root = r"/mnt/c/Users/ikene/Documents/spider"
    gitignore_path = os.path.join(spider_root, ".gitignore")
    
    if not os.path.exists(spider_root):
        print(f"spider directory not found: {spider_root}")
        return
    
    patterns = load_gitignore_patterns(gitignore_path)
    print(f"{spider_root}/")
    
    # list all items in root directory
    root_dir = Path(spider_root)
    try:
        items = sorted([item for item in root_dir.iterdir() 
                      if not should_ignore(item, patterns)])
    except PermissionError:
        print("permission denied accessing spider directory")
        return
    
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1)
        list_directory_tree(item, patterns, "", is_last)

if __name__ == "__main__":
    main()