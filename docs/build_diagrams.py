from os import listdir, remove
from os.path import join
import subprocess as sp
import sys

if(len(sys.argv) < 1 or sys.argv[1] == "--help" or sys.argv[1] == "-h"):
    print("Usage: python build_diagrams.py [config_path] [dir_path] [format]",
          "Defaults: confog_path='.', dir_path='.', format='png'")
    exit()

format_ext = sys.argv[3] if len(sys.argv) > 3 else "png"
dir_path = sys.argv[2] if len(sys.argv) > 2 else "."
config_path = sys.argv[1] if len(sys.argv) > 1 else "."

md_files = [file for file in listdir(dir_path) if file.endswith(".md")]

for md_file in md_files:
    mmd_file = md_file.replace(".md", ".mmd")
    out_file = md_file.replace(".md", f".{format_ext}")
    lines = []
    with open(join(dir_path, md_file), "r") as f:
        lines = f.readlines()
    with open(join(dir_path, mmd_file), "w") as f:
        f.writelines(lines[1:-1])

    print(f'Processing {md_file}...')
    sp.run(
        ['mmdc',
         '-p',
         join(config_path, 'mmdc_config.json'),
         '-i',
         join(dir_path, mmd_file),
         '-o',
         join(dir_path, out_file)]
    )
    print(f'Done {md_file}')
    
    remove(join(dir_path, mmd_file))
