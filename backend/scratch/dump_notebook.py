import json
import sys
import os

def dump_notebook(nb_path, py_path):
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    
    code_lines = []
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            code_lines.append(f"# ==========================================\n# CELL {i}\n# ==========================================\n")
            code_lines.append("".join(cell['source']))
            code_lines.append("\n\n")
            
    with open(py_path, 'w', encoding='utf-8') as f:
        f.writelines(code_lines)
    print(f"Successfully dumped {nb_path} to {py_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python dump_notebook.py <input.ipynb> <output.py>")
    else:
        dump_notebook(sys.argv[1], sys.argv[2])
