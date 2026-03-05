import ast

with open('main.py') as f:
    content = f.read()

tree = ast.parse(content)

for node in tree.body:
    if isinstance(node, ast.ClassDef):
        bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
        print(f"Class: {node.name}, Bases: {bases}, Lines: {node.lineno}-{node.end_lineno}")
