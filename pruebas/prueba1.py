import tkinter as tk
from tkinter import messagebox
import pyodbc
import json

# Configuración de conexión a SQL Server
DB_CONFIG = {
    'Driver': '{SQL Server}',
    'Server': 'CHALI\\SQLEXPRESS',
    'Database': 'bdRestaurante',
    'UID': 'camarero',
    'PWD': 'cam1234'
}

# Conectar a la base de datos
def conectar_bd():
    return pyodbc.connect(
        f"DRIVER={DB_CONFIG['Driver']};SERVER={DB_CONFIG['Server']};DATABASE={DB_CONFIG['Database']};UID={DB_CONFIG['UID']};PWD={DB_CONFIG['PWD']}"
    )

# Obtener lista de productos
def obtener_productos():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM Productos")
    productos = cursor.fetchall()
    conn.close()
    return productos

# Obtener lista de mesas disponibles
def obtener_mesas():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT id, numero_mesa FROM Mesas WHERE estado = 'Disponible'")
    mesas = cursor.fetchall()
    conn.close()
    return mesas

# Enviar pedido al procedimiento almacenado
def enviar_pedido():
    mesa_id = mesa_var.get()
    estado = "Pendiente"

    # Preparar productos seleccionados
    productos_detalles = []
    for producto_id, cantidad_entry in entradas_productos.items():
        cantidad = cantidad_entry.get()
        if cantidad and int(cantidad) > 0:
            productos_detalles.append({"producto_id": producto_id, "cantidad": int(cantidad)})

    if not productos_detalles:
        messagebox.showwarning("Error", "Debes seleccionar al menos un producto con cantidad.")
        return

    productos_json = json.dumps(productos_detalles)

    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("EXEC InsertarPedidoCompleto ?, ?, ?", (mesa_id, estado, productos_json))
        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", "Pedido enviado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"Error al insertar pedido: {e}")

# Crear ventana principal
root = tk.Tk()
root.title("Sistema de Pedidos")
root.geometry("400x400")

# Selección de mesa
tk.Label(root, text="Selecciona Mesa:").pack()
mesa_var = tk.IntVar()
mesas = obtener_mesas()
for mesa_id, numero_mesa in mesas:
    tk.Radiobutton(root, text=f"Mesa {numero_mesa}", variable=mesa_var, value=mesa_id).pack()

# Selección de productos y cantidades
tk.Label(root, text="Selecciona Productos:").pack()
productos = obtener_productos()
entradas_productos = {}

for producto_id, nombre_producto in productos:
    frame = tk.Frame(root)
    frame.pack()
    tk.Label(frame, text=nombre_producto).pack(side="left")
    cantidad_entry = tk.Entry(frame, width=5)
    cantidad_entry.pack(side="right")
    entradas_productos[producto_id] = cantidad_entry

# Botón para enviar pedido
tk.Button(root, text="Enviar Pedido", command=enviar_pedido).pack()

# Iniciar la aplicación
root.mainloop()
