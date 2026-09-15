"""
execute_gt_nb.py
================
Mengeksekusi seluruh sel dalam notebook ground truth agar output,
grafik matplotlib/seaborn, tabel pandas, dan peta Leaflet tersimpan rapi.
"""

import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import nbformat
from nbclient import NotebookClient
from nbformat import sign

nb_path = 'notebooks/02_visualisasi_ground_truth_lengkap.ipynb'
print(f"Loading notebook: {nb_path}")
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

client = NotebookClient(nb, timeout=300, kernel_name='python3')
print("Executing ground truth notebook cells...")
client.execute()

with open(nb_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

# Sign notebook
notary = sign.NotebookNotary()
notary.sign(nb)

print(f"Ground truth notebook successfully executed, saved, and signed: {nb_path}")
