"""
execute_nb.py
=============
Mengeksekusi seluruh sel dalam notebook agar seluruh output,
grafik matplotlib, tabel metrik, dan peta Folium tersimpan di file .ipynb.
"""

import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import nbformat
from nbclient import NotebookClient

nb_path = 'notebooks/01_evaluasi_metode_dan_hasil_knndtw.ipynb'
print(f"Loading notebook: {nb_path}")
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

client = NotebookClient(nb, timeout=300, kernel_name='python3')
print("Executing notebook cells...")
client.execute()

with open(nb_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print(f"Notebook successfully executed and saved: {nb_path}")
