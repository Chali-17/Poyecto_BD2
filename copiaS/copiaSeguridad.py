import subprocess
import os

# Obtener la ruta absoluta del directorio donde está este script
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construir la ruta al archivo BAT de forma relativa
bat_path = os.path.join(base_dir, 'copiaS', 'seguridad.bat')

try:
    # Ejecutar el archivo BAT
    result = subprocess.run([bat_path], shell=True, check=True)
    print("Copia de seguridad ejecutada correctamente.")
except subprocess.CalledProcessError as e:
    print(f"Error al ejecutar la copia de seguridad: {e}")
except FileNotFoundError:
    print("No se encontró el archivo seguridad.bat en la carpeta copiaS.")