from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pyodbc, json

from io import BytesIO
from flask import send_file

app = Flask(__name__)
app.secret_key = '16'  # Clave secreta para sesiones

# Configuración de conexión a SQL Server
DB_CONFIG = {
    'Driver': '{SQL Server}',
    'Server': 'AsusF15Eddy\SQLEXPRESS',
    'Database': 'bdRestaurante'
}

# Función para obtener conexión a la base de datos
def get_db_connection(username, password):
    conn_str = f"Driver={DB_CONFIG['Driver']};Server={DB_CONFIG['Server']};Database={DB_CONFIG['Database']};UID={username};PWD={password}"
    return pyodbc.connect(conn_str)

# Página de login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        if not role or not username or not password:
            return render_template('login.html', error_message='Todos los campos son obligatorios')

        try:
            conn = get_db_connection(username, password)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sys.database_principals WHERE name = ?", (role,))
            user_role = cursor.fetchone()

            if user_role:
                session['user_role'] = role
                session['username'] = username
                session['password'] = password

                cursor.execute("EXEC inicioSesion @Usuario = ?", (username,))
                conn.commit()
                cursor.close()
                conn.close()

                return redirect(url_for(f'{role}_home'))
            else:
                cursor.close()
                conn.close()
                return render_template('login.html', error_message='Rol seleccionado no válido')

        except Exception as e:
            print(f"Error de conexión: {e}")
            return render_template('login.html', error_message='Usuario o contraseña incorrectos')

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    try:
        if 'username' in session and 'password' in session:
            conn = get_db_connection(session['username'], session['password'])
            cursor = conn.cursor()
            cursor.execute("EXEC cerrarSesion @Usuario = ?", session['username'])
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error al registrar logout: {e}")

    session.clear()
    return redirect(url_for('login'))

# Panel de administrador
@app.route('/admin')
def adminRes_home():
    if session.get('user_role') != 'adminRes':
        return redirect(url_for('login'))

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('''
            SELECT p.id, p.nombre, p.precio, c.nombre AS categoria_nombre, p.categoria_id
            FROM Productos p
            JOIN Categoria c ON p.categoria_id = c.id
        ''')
        productos = cursor.fetchall()

        cursor.execute('SELECT id, nombre FROM Categoria')
        categorias = cursor.fetchall()

        cursor.execute('SELECT id, numero_mesa, estado FROM Mesas')
        mesas = cursor.fetchall()

        contador_disponible = sum(1 for m in mesas if m.estado == 'Disponible')
        contador_ocupada = sum(1 for m in mesas if m.estado == 'Ocupada')
        contador_reservada = sum(1 for m in mesas if m.estado == 'Reservada')

        cursor.close()
        conn.close()

        return render_template('admin_home.html', productos=productos, categorias=categorias, mesas=mesas, contador_disponible=contador_disponible, contador_ocupada=contador_ocupada, contador_reservada=contador_reservada)
    except Exception as e:
        print(f"Error en admin panel: {e}")
        return render_template('admin_home.html', productos=[], categorias=[], mesas=[], error="Error al cargar los datos.")

@app.route('/admin/productos/agregar', methods=['POST'])
def agregar_producto():
    if session.get('user_role') != 'adminRes':
        return jsonify({'status': 'error', 'message': 'No autorizado'})

    nombre = request.form['nombre']
    precio = request.form['precio']
    categoria_id = request.form['categoria_id']

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('SELECT nombre FROM Categoria WHERE id = ?', (categoria_id,))
        categoria_nombre = cursor.fetchone()[0]

        cursor.execute('INSERT INTO Productos (nombre, precio, categoria_id) VALUES (?, ?, ?)',
                       (nombre, precio, categoria_id))
        conn.commit()

        cursor.execute('SELECT TOP 1 id FROM Productos WHERE nombre = ? ORDER BY id DESC', (nombre,))
        prod_id = cursor.fetchone()[0]

        # Auditoría
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Agregó producto "{nombre}"'))
        conn.commit()

        return jsonify({
            'status': 'success',
            'message': f'Producto "{nombre}" agregado.',
            'producto': {
                'id': prod_id,
                'nombre': nombre,
                'precio': float(precio),
                'categoria_id': int(categoria_id),
                'categoria_nombre': categoria_nombre
            }
        })

    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Error al agregar producto'})

@app.route('/admin/productos/eliminar', methods=['POST'])
def eliminar_producto():
    if session.get('user_role') != 'adminRes':
        return jsonify({'status': 'error', 'message': 'No autorizado'})

    producto_id = request.form.get('id')

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('SELECT nombre FROM Productos WHERE id = ?', (producto_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'status': 'error', 'message': 'Producto no encontrado'})
        nombre = row[0]

        cursor.execute('DELETE FROM Productos WHERE id = ?', (producto_id,))
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Eliminó producto "{nombre}"'))
        conn.commit()

        return jsonify({'status': 'success', 'message': f'Producto eliminado.', 'id': producto_id})

    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Error al eliminar'})


# Editar producto
@app.route('/admin/productos/editar/<int:id>', methods=['POST'])
def editar_producto(id):
    if session.get('user_role') != 'adminRes':
        return jsonify({'status': 'error', 'message': 'No autorizado'})

    nombre_nuevo = request.form['nombre']
    precio_nuevo = float(request.form['precio'])
    categoria_id_nueva = int(request.form['categoria_id'])

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        # Obtener datos actuales
        cursor.execute('''
            SELECT p.nombre, p.precio, c.nombre, p.categoria_id
            FROM Productos p
            JOIN Categoria c ON p.categoria_id = c.id
            WHERE p.id = ?
        ''', (id,))
        original = cursor.fetchone()
        if not original:
            return jsonify({'status': 'error', 'message': 'Producto no encontrado'})

        nombre_original, precio_original, categoria_nombre_original, categoria_id_original = original

        # Actualizar producto
        cursor.execute('''
            UPDATE Productos
            SET nombre = ?, precio = ?, categoria_id = ?
            WHERE id = ?
        ''', (nombre_nuevo, precio_nuevo, categoria_id_nueva, id))

        # Obtener nueva categoría (para auditoría)
        cursor.execute('SELECT nombre FROM Categoria WHERE id = ?', (categoria_id_nueva,))
        nueva_categoria_nombre = cursor.fetchone()[0]

        # Registro en auditoría (solo si cambió algo)
        if nombre_nuevo != nombre_original:
            cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)', (
                session['username'],
                f'Editó producto ID {id}: nombre de "{nombre_original}" a "{nombre_nuevo}"'
            ))

        if precio_nuevo != precio_original:
            cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)', (
                session['username'],
                f'Editó producto ID {id}: precio de {precio_original} a {precio_nuevo}'
            ))

        if categoria_id_nueva != categoria_id_original:
            cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)', (
                session['username'],
                f'Editó producto ID {id}: categoría de "{categoria_nombre_original}" a "{nueva_categoria_nombre}"'
            ))

        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Producto actualizado.',
            'producto': {
                'id': id,
                'nombre': nombre_nuevo,
                'precio': precio_nuevo,
                'categoria_id': categoria_id_nueva,
                'categoria_nombre': nueva_categoria_nombre
            }
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': 'Error inesperado'})



@app.route('/admin/categorias/agregar', methods=['POST'])
def agregar_categoria_ajax():
    if session.get('user_role') != 'adminRes':
        return jsonify({'status': 'error', 'message': 'No autorizado'})

    nombre = request.form['nombre'].strip()

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM Categoria WHERE nombre = ?', (nombre,))
        if cursor.fetchone()[0] > 0:
            return jsonify({'status': 'error', 'message': 'Ya existe esa categoría.'})

        cursor.execute('INSERT INTO Categoria (nombre) VALUES (?)', (nombre,))
        conn.commit()

        cursor.execute('SELECT TOP 1 id FROM Categoria WHERE nombre = ? ORDER BY id DESC', (nombre,))
        cat_id = cursor.fetchone()[0]

        # Auditoría
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Agregó categoría "{nombre}"'))
        conn.commit()

        return jsonify({'status': 'success', 'message': f'Categoría "{nombre}" agregada.', 'categoria': {'id': cat_id, 'nombre': nombre}})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Error al agregar categoría'})


@app.route('/admin/categorias/editar/<int:id>', methods=['POST'])
def editar_categoria(id):
    if session.get('user_role') != 'adminRes':
        return jsonify({'status': 'error', 'message': 'No autorizado'})

    nuevo_nombre = request.form.get('nombre')

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        # Obtener nombre actual
        cursor.execute('SELECT nombre FROM Categoria WHERE id = ?', (id,))
        actual = cursor.fetchone()
        if not actual:
            return jsonify({'status': 'error', 'message': 'Categoría no encontrada'})

        nombre_actual = actual[0]

        # Actualizar solo si es diferente
        if nuevo_nombre != nombre_actual:
            cursor.execute('UPDATE Categoria SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
            cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)', (
                session['username'],
                f'Editó categoría ID {id}: nombre de "{nombre_actual}" a "{nuevo_nombre}"'
            ))

        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Categoría actualizada.',
            'categoria': {'id': id, 'nombre': nuevo_nombre}
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': 'Error inesperado'})

@app.route('/admin/categorias/eliminar', methods=['POST'])
def eliminar_categoria_ajax():
    if session.get('user_role') != 'adminRes':
        return jsonify({'status': 'error', 'message': 'No autorizado'})

    cat_id = request.form.get('id')

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM Productos WHERE categoria_id = ?', (cat_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'status': 'error', 'message': 'No se puede eliminar: hay productos asociados.'})

        cursor.execute('SELECT nombre FROM Categoria WHERE id = ?', (cat_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'status': 'error', 'message': 'Categoría no encontrada'})
        nombre = row[0]

        cursor.execute('DELETE FROM Categoria WHERE id = ?', (cat_id,))
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Eliminó categoría "{nombre}"'))
        conn.commit()

        return jsonify({'status': 'success', 'message': 'Categoría eliminada.', 'id': cat_id})
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Error inesperado al eliminar'})


@app.route('/admin/mesas/agregar', methods=['POST'])
def agregar_mesa_ajax():
    if session.get('user_role') != 'adminRes':
        return jsonify({'status': 'error', 'message': 'No autorizado'})

    numero_mesa = request.form.get('numero_mesa')
    try:
        numero_mesa = int(numero_mesa)
    except:
        return jsonify({'status': 'error', 'message': 'Número inválido'})

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM Mesas WHERE numero_mesa = ?', (numero_mesa,))
        if cursor.fetchone()[0] > 0:
            return jsonify({'status': 'error', 'message': f'Ya existe la mesa {numero_mesa}.'})

        cursor.execute('INSERT INTO Mesas (numero_mesa, estado) VALUES (?, ?)', (numero_mesa, 'Disponible'))
        conn.commit()

        cursor.execute('SELECT TOP 1 id FROM Mesas WHERE numero_mesa = ? ORDER BY id DESC', (numero_mesa,))
        mesa_id = int(cursor.fetchone()[0])

        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Agregó mesa {numero_mesa}'))
        conn.commit()

        return jsonify({
            'status': 'success',
            'message': f'Mesa {numero_mesa} agregada correctamente.',
            'mesa': {'id': mesa_id, 'numero_mesa': numero_mesa, 'estado': 'Disponible'}
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': 'Error inesperado'})




@app.route('/admin/mesas/eliminar', methods=['POST'])
def eliminar_mesa_ajax():
    if session.get('user_role') != 'adminRes':
        return jsonify({'status': 'error', 'message': 'No autorizado'})

    mesa_id = request.form.get('id')

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('SELECT numero_mesa FROM Mesas WHERE id = ?', (mesa_id,))
        mesa = cursor.fetchone()
        if not mesa:
            return jsonify({'status': 'error', 'message': 'Mesa no encontrada'})

        numero = mesa[0]

        cursor.execute('DELETE FROM Mesas WHERE id = ?', (mesa_id,))
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Eliminó mesa {numero}'))

        conn.commit()
        return jsonify({'status': 'success', 'message': f'Mesa {numero} eliminada correctamente.', 'id': mesa_id})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': 'Error inesperado'})



# Rutas por rol (home)
@app.route('/camarero')
def camarero_home():
    if session.get('user_role') != 'camarero':
        return redirect(url_for('login'))

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        # Obtener mesas disponibles
        cursor.execute("SELECT id, numero_mesa, estado FROM Mesas WHERE estado = 'Disponible'")
        mesas = cursor.fetchall()

        # Obtener productos
        cursor.execute("SELECT id, nombre, precio FROM Productos")
        productos = cursor.fetchall()

        # Obtener pedidos activos (Pendiente o Preparando) con sus productos
        cursor.execute("""
            SELECT 
                p.id AS pedido_id,
                m.numero_mesa,
                p.estado,
                pr.nombre AS nombre_producto,
                dp.cantidad
            FROM Pedidos p
            JOIN Mesas m ON m.id = p.mesa_id
            JOIN Detalle_Pedidos dp ON dp.pedido_id = p.id
            JOIN Productos pr ON pr.id = dp.producto_id
            WHERE p.estado IN ('Pendiente', 'Preparando')
            ORDER BY p.id DESC
        """)
        rows = cursor.fetchall()

        # Agrupar productos por pedido
        pedidos_dict = {}
        for row in rows:
            pid = row.pedido_id
            if pid not in pedidos_dict:
                pedidos_dict[pid] = {
                    'pedido_id': pid,
                    'mesa': row.numero_mesa,
                    'estado': row.estado,
                    'productos': []
                }
            pedidos_dict[pid]['productos'].append({
                'nombre': row.nombre_producto,
                'cantidad': row.cantidad
            })

        pedidos_agrupados = list(pedidos_dict.values())

        cursor.close()
        conn.close()

        return render_template('camarero_home.html',
                               mesas=mesas,
                               productos=productos,
                               pedidos_activos=pedidos_agrupados)

    except Exception as e:
        print(f"Error en camarero_home: {e}")
        return render_template('camarero_home.html',
                               mesas=[], productos=[], pedidos_activos=[])



@app.route('/camarero/orden', methods=['POST'])
def tomar_orden():
    if session.get('user_role') != 'camarero':
        return redirect(url_for('login'))

    mesa_id = request.form.get('mesa_id')
    productos_id = request.form.getlist('producto_id[]')
    cantidades = request.form.getlist('cantidad[]')

    productos_detalles = []

    for pid, cant in zip(productos_id, cantidades):
        if pid and cant and int(cant) > 0:
            productos_detalles.append({"producto_id": int(pid), "cantidad": int(cant)})

    if not productos_detalles:
        flash("Debe seleccionar al menos un producto con cantidad válida.", "error")
        return redirect(url_for('camarero_home'))

    productos_json = json.dumps(productos_detalles)

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()
        cursor.execute("EXEC InsertarPedidoCompleto ?, ?, ?", (mesa_id, 'Pendiente', productos_json))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Pedido registrado correctamente", "success")
    except Exception as e:
        flash(f"Error al registrar pedido: {e}", "error")

    return redirect(url_for('camarero_home'))

@app.route('/cocina')
def cocina_home():
    if session.get('user_role') != 'cocina':
        return redirect(url_for('login'))

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        def agrupar_pedidos(rows):
            pedidos_dict = {}
            for row in rows:
                pid = row.pedido_id
                if pid not in pedidos_dict:
                    pedidos_dict[pid] = {
                        'pedido_id': pid,
                        'mesa': row.numero_mesa,
                        'estado': row.estado,
                        'productos': []
                    }
                pedidos_dict[pid]['productos'].append({
                    'nombre': row.nombre_producto,
                    'cantidad': row.cantidad
                })
            return list(pedidos_dict.values())

        # Activos
        # Pedidos activos usando vistaCocina (solo estado 'Pendiente')
        cursor.execute("""
            SELECT vc.id AS pedido_id, m.numero_mesa, vc.estado,
                pr.nombre AS nombre_producto, dp.cantidad
            FROM vistaCocina vc
            JOIN Mesas m ON m.id = vc.mesa_id
            JOIN Detalle_Pedidos dp ON dp.pedido_id = vc.id
            JOIN Productos pr ON pr.id = dp.producto_id
            ORDER BY vc.id DESC
        """)
        pedidos_activos = agrupar_pedidos(cursor.fetchall())


        # Servidos
        cursor.execute("""
            SELECT p.id AS pedido_id, m.numero_mesa, p.estado, pr.nombre AS nombre_producto, dp.cantidad
            FROM Pedidos p
            JOIN Mesas m ON m.id = p.mesa_id
            JOIN Detalle_Pedidos dp ON dp.pedido_id = p.id
            JOIN Productos pr ON pr.id = dp.producto_id
            WHERE p.estado = 'Servido'
            ORDER BY p.id DESC
        """)
        pedidos_servidos = agrupar_pedidos(cursor.fetchall())

        # Archivados
        cursor.execute("""
            SELECT p.id AS pedido_id, m.numero_mesa, p.estado, pr.nombre AS nombre_producto, dp.cantidad
            FROM Pedidos p
            JOIN Mesas m ON m.id = p.mesa_id
            JOIN Detalle_Pedidos dp ON dp.pedido_id = p.id
            JOIN Productos pr ON pr.id = dp.producto_id
            WHERE p.estado = 'Archivado'
            ORDER BY p.id DESC
        """)
        pedidos_archivados = agrupar_pedidos(cursor.fetchall())

        cursor.close()
        conn.close()

        return render_template('cocina_home.html',
                               pedidos=pedidos_activos,
                               pedidos_servidos=pedidos_servidos,
                               pedidos_archivados=pedidos_archivados)

    except Exception as e:
        print(f"Error en cocina_home: {e}")
        return render_template('cocina_home.html',
                               pedidos=[], pedidos_servidos=[], pedidos_archivados=[])

    
@app.route('/cocina/estado', methods=['POST'])
def actualizar_estado_pedido():
    if session.get('user_role') != 'cocina':
        return jsonify({'status': 'error', 'message': 'No autorizado'})

    data = request.get_json()
    pedido_id = data.get('pedido_id')
    nuevo_estado = data.get('estado')

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute("UPDATE Pedidos SET estado = ? WHERE id = ?", (nuevo_estado, pedido_id))

        cursor.execute("INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)",
                       (session['username'], f'Cocinero actualizó Pedido #{pedido_id} a estado "{nuevo_estado}"'))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'message': f'Pedido actualizado a {nuevo_estado}.'})

    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Error al actualizar estado'})


@app.route('/cajero')
def cajero_home():
    if session.get('user_role') != 'cajero':
        return redirect(url_for('login'))

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        # Usar vistaCajero para obtener solo pedidos servidos
        cursor.execute("""
            SELECT vc.id AS pedido_id, m.numero_mesa, vc.estado,
                   pr.nombre AS nombre_producto, dp.cantidad,
                   pr.precio * dp.cantidad AS subtotal
            FROM vistaCajero vc
            JOIN Mesas m ON m.id = vc.mesa_id
            JOIN Detalle_Pedidos dp ON dp.pedido_id = vc.id
            JOIN Productos pr ON pr.id = dp.producto_id
            ORDER BY vc.id DESC
        """)
        rows = cursor.fetchall()

        # Agrupar productos por pedido
        pedidos_dict = {}
        for row in rows:
            pid = row.pedido_id
            if pid not in pedidos_dict:
                pedidos_dict[pid] = {
                    'pedido_id': pid,
                    'mesa': row.numero_mesa,
                    'estado': row.estado,
                    'productos': [],
                    'total': 0
                }
            pedidos_dict[pid]['productos'].append({
                'nombre': row.nombre_producto,
                'cantidad': row.cantidad,
                'subtotal': row.subtotal
            })
            pedidos_dict[pid]['total'] += row.subtotal

        pedidos = list(pedidos_dict.values())

        cursor.close()
        conn.close()

        return render_template('cajero_home.html', pedidos=pedidos)

    except Exception as e:
        print(f"Error en cajero_home: {e}")
        return render_template('cajero_home.html', pedidos=[])

    

from flask import jsonify
import subprocess
import sys
import os

@app.route('/admin/copia_seguridad', methods=['POST'])
def copia_seguridad():
    import subprocess
    import os

    base_dir = os.path.dirname(os.path.abspath(__file__))
    bat_path = os.path.join(base_dir, 'copiaS', 'seguridad.bat')

    try:
        result = subprocess.run([bat_path], shell=True, check=True)
        # Insertar en Auditoría
        try:
            conn = get_db_connection(session['username'], session['password'])
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)', (
                session['username'],
                'Realizó una copia de seguridad'
            ))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error al registrar en auditoría: {e}")
        return jsonify({"status": "success", "message": "Copia de seguridad ejecutada correctamente."})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"Error al ejecutar la copia de seguridad: {e}"})
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "No se encontró el archivo seguridad.bat en la carpeta copiaS."})

@app.route('/admin/reporte_auditoria_pdf')
def reporte_auditoria_pdf():
    if session.get('user_role') != 'adminRes':
        return "No autorizado", 403

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()
        cursor.execute('SELECT UsuarioSys, accion, fecha FROM Auditoria ORDER BY fecha DESC')
        auditoria = cursor.fetchall()
        # Registrar la acción de generación de reporte en la auditoría
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], 'Generó reporte de auditoría en PDF'))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al obtener auditoría: {e}")
        return "Error al generar el reporte", 500

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 40, "Reporte de Auditoría")
    p.setFont("Helvetica", 10)
    y = height - 70
    p.drawString(40, y, "N°")
    p.drawString(70, y, "Usuario")
    p.drawString(210, y, "Acción")
    p.drawString(430, y, "Fecha")
    y -= 15
    p.line(40, y, 570, y)
    y -= 15

    fila = 1
    for usuario, accion, fecha in auditoria:
        if y < 50:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 10)
        p.drawString(40, y, str(fila))
        p.drawString(70, y, str(usuario))
        p.drawString(210, y, str(accion))
        p.drawString(430, y, str(fecha))
        y -= 15
        fila += 1

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reporte_auditoria.pdf", mimetype='application/pdf')

# Ejecutar la app
if __name__ == '__main__':
    app.run(debug=True)



