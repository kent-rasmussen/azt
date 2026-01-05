import re
import os

files_to_check = [
    'main.py',
    'ui_tkinter.py',
    'lift.py',
    'alphabet_chart.py',
    'parser.py'
]

def verify_files():
    found_issues = False
    for filename in files_to_check:
        filepath = os.path.join('/home/kentr/bin/raspy/azt/', filename)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Find all _(...) calls using word boundary to avoid __init__(
        matches = re.finditer(r'\b_\((.*?)\)', content, re.DOTALL)
        for match in matches:
            inner = match.group(1)
            # Check for f-strings
            if re.search(r'^f["\']', inner.strip()):
                found_issues = True
                line_no = content.count('\n', 0, match.start()) + 1
                print(f"Issue in {filename}:{line_no}: f-string inside _()")
                print(f"  Content: _({inner.strip()})")
            
            # Check for positional {}
            if '{}' in inner:
                found_issues = True
                line_no = content.count('\n', 0, match.start()) + 1
                print(f"Issue in {filename}:{line_no}: positional {{}} inside _()")
                print(f"  Content: _({inner.strip()})")
                
            # Check for .format() inside _()
            if '.format(' in inner:
                found_issues = True
                line_no = content.count('\n', 0, match.start()) + 1
                print(f"Issue in {filename}:{line_no}: .format() inside _()")
                print(f"  Content: _({inner.strip()})")

    if not found_issues:
        print("No issues found! All files passed verification.")
    else:
        print("Verification failed. Please fix the issues listed above.")

if __name__ == "__main__":
    verify_files()
