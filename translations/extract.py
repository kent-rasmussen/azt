#!/usr/bin/env python3
import os
import subprocess
import sys

def extract_strings():
    """
    Scans the project for Python files and extracts translatable strings
    into translations/azt.pot using xgettext.
    """
    # Determine directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) # Assumes translations/ is one level deep
    output_file = os.path.join(script_dir, 'azt.pot')
    temp_output_file = os.path.join(script_dir, 'azt.pot.tmp')

    print(f"Project root: {project_root}")
    print(f"Output file: {output_file}")

    # Find all python files
    files_to_scan = []
    for root, dirs, files in os.walk(project_root):
        # Skip hidden directories and virtual environments
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('env', 'venv', '__pycache__')]
        
        for file in files:
            if file.endswith('.py'):
                files_to_scan.append(os.path.join(root, file))

    if not files_to_scan:
        print("No Python files found to scan.")
        return

    print(f"Found {len(files_to_scan)} Python files.")

    # Construct xgettext command
    cmd = [
        'xgettext',
        '--language=Python',
        '--keyword=_',
        '--from-code=UTF-8',
        '--sort-output',
        '--output', temp_output_file,
    ] + files_to_scan

    print("Running xgettext...")
    try:
        subprocess.run(cmd, check=True)
        
        # Check if we should update the file
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                old_content = f.read()
            with open(temp_output_file, 'r', encoding='utf-8') as f:
                new_content = f.read()
            
            # Remove POT-Creation-Date for comparison
            import re
            pattern = re.compile(r'"POT-Creation-Date: .*?\\n"')
            old_content_clean = pattern.sub('', old_content)
            new_content_clean = pattern.sub('', new_content)
            
            if old_content_clean == new_content_clean:
                print("No changes detected (ignoring POT-Creation-Date). Skipping update.")
                os.remove(temp_output_file)
                return
            else:
                print("Changes detected.")
        
        os.replace(temp_output_file, output_file)
        print(f"Successfully updated {output_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running xgettext: {e}")
        if os.path.exists(temp_output_file):
            os.remove(temp_output_file)
    except FileNotFoundError:
        print("Error: xgettext not found. Please install gettext.")

if __name__ == "__main__":
    extract_strings()
