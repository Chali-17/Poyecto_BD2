from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pyodbc

app = Flask(__name__)
app.secret_key = '16'  # Clave secreta para sesiones

# Configuración de conexión a SQL Server
DB_CONFIG = {
    'Driver': '{SQL Server}',
    'Server': 'AsusF15Eddy\\SQLEXPRESS',
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
    return render_template('camarero_home.html')

@app.route('/cajero')
def cajero_home():
    if session.get('user_role') != 'cajero':
        return redirect(url_for('login'))
    return render_template('cajero_home.html')

@app.route('/cocina')
def cocina_home():
    if session.get('user_role') != 'cocina':
        return redirect(url_for('login'))
    return render_template('cocina_home.html')
    

# Ejecutar la app
if __name__ == '__main__':
    app.run(debug=True)




