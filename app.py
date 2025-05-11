from flask import Flask, render_template, request, redirect, url_for, session
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

# Agregar producto
@app.route('/admin/productos/agregar', methods=['POST'])
def agregar_producto():
    if session.get('user_role') != 'adminRes':
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    precio = request.form['precio']
    categoria_id = request.form['categoria_id']

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO Productos (nombre, precio, categoria_id)
            VALUES (?, ?, ?)
        ''', (nombre, precio, categoria_id))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al agregar producto: {e}")

    return redirect(url_for('adminRes_home'))

# Eliminar producto
@app.route('/admin/productos/eliminar', methods=['GET'])
def eliminar_producto():
    if session.get('user_role') != 'adminRes':
        return redirect(url_for('login'))

    id = request.args.get('id')
    if not id:
        return redirect(url_for('adminRes_home'))

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()
        cursor.execute('SELECT nombre FROM Productos WHERE id = ?', (id,))
        producto = cursor.fetchone()
        nombre = producto[0] if producto else 'desconocido'

        cursor.execute('DELETE FROM Productos WHERE id = ?', (id,))
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Eliminó el producto ID {id} → "{nombre}"'))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al eliminar producto: {e}")

    return redirect(url_for('adminRes_home'))

# Editar producto
@app.route('/admin/productos/editar/<int:id>', methods=['POST'])
def editar_producto(id):
    if session.get('user_role') != 'adminRes':
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    precio = request.form['precio']
    categoria_id = request.form['categoria_id']

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE Productos
            SET nombre = ?, precio = ?, categoria_id = ?
            WHERE id = ?
        ''', (nombre, precio, categoria_id, id))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al editar producto: {e}")

    return redirect(url_for('adminRes_home'))

@app.route('/admin/categorias/agregar', methods=['POST'])
def agregar_categoria():
    if session.get('user_role') != 'adminRes':
        return redirect(url_for('login'))
    
    nombre = request.form['nombre']
    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()
        cursor.execute('INSERT INTO Categoria (nombre) VALUES (?)', (nombre,))
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Agregó categoría "{nombre}"'))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al agregar categoría: {e}")

    return redirect(url_for('adminRes_home'))

@app.route('/admin/categorias/editar/<int:id>', methods=['POST'])
def editar_categoria(id):
    if session.get('user_role') != 'adminRes':
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()
        cursor.execute('UPDATE Categoria SET nombre = ? WHERE id = ?', (nombre, id))
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Editó categoría ID {id} → "{nombre}"'))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al editar categoría: {e}")

    return redirect(url_for('adminRes_home'))

@app.route('/admin/categorias/eliminar', methods=['GET'])
def eliminar_categoria():
    if session.get('user_role') != 'adminRes':
        return redirect(url_for('login'))

    id = request.args.get('id')
    if not id:
        return redirect(url_for('adminRes_home'))

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()
        cursor.execute('SELECT nombre FROM Categoria WHERE id = ?', (id,))
        cat = cursor.fetchone()
        nombre = cat[0] if cat else 'desconocida'

        cursor.execute('DELETE FROM Categoria WHERE id = ?', (id,))
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Eliminó categoría ID {id} → "{nombre}"'))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al eliminar categoría: {e}")

    return redirect(url_for('adminRes_home'))

@app.route('/admin/mesas/agregar', methods=['POST'])
def agregar_mesa():
    if session.get('user_role') != 'adminRes':
        return redirect(url_for('login'))

    numero_mesa = request.form['numero_mesa']
    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        cursor.execute('INSERT INTO Mesas (numero_mesa, estado) VALUES (?, ?)', (numero_mesa, 'Disponible'))
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Agregó mesa número {numero_mesa}'))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al agregar mesa: {e}")

    return redirect(url_for('adminRes_home'))

@app.route('/admin/mesas/eliminar', methods=['GET'])
def eliminar_mesa():
    if session.get('user_role') != 'adminRes':
        return redirect(url_for('login'))

    id = request.args.get('id')
    if not id:
        return redirect(url_for('adminRes_home'))

    try:
        conn = get_db_connection(session['username'], session['password'])
        cursor = conn.cursor()

        # Obtener el número de la mesa
        cursor.execute('SELECT numero_mesa FROM Mesas WHERE id = ?', (id,))
        mesa = cursor.fetchone()
        numero = mesa[0] if mesa else 'desconocida'

        # Eliminar la mesa
        cursor.execute('DELETE FROM Mesas WHERE id = ?', (id,))
        cursor.execute('INSERT INTO Auditoria (UsuarioSys, accion) VALUES (?, ?)',
                       (session['username'], f'Eliminó mesa ID {id} → número {numero}'))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error al eliminar mesa: {e}")

    return redirect(url_for('adminRes_home'))


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




