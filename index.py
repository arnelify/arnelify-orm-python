import os
import subprocess

dist_folder = './dist'
whl_files = [f for f in os.listdir(dist_folder) if f.endswith('.whl')]

if whl_files:
  for whl_file in whl_files:
    file_path = os.path.join(dist_folder, whl_file)
    command = f'venv/bin/pip install --force-reinstall {file_path}'
    subprocess.run(command, shell=True, check=True)
else:
    print('Can\'t find *.whl-file')