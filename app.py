from flask import Flask, render_template, request, redirect, url_for, flash, session
import pyodbc

app = Flask(__name__)
app.secret_key = '16'  # Needed for flash messages

# Database connection configuration
DB_CONFIG = {
    'Driver': '{SQL Server}',
    #'Server': 'AsusF15Eddy\SQLEXPRESS',
    'Server': 'CHALI\SQLEXPRESS',
    'Database': 'bdRestaurante'
}

def get_db_connection(username, password):
    conn_str = f'Driver={DB_CONFIG["Driver"]};Server={DB_CONFIG["Server"]};Database={DB_CONFIG["Database"]};UID={username};PWD={password}'
    return pyodbc.connect(conn_str)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate that all fields are filled
        if not role or not username or not password:
            return render_template('login.html', error_message='Todos los campos son obligatorios')

        try:
            # Try to establish connection with provided credentials
            conn = get_db_connection(username, password)
            cursor = conn.cursor()
            
            # Verify if username matches the selected role
            cursor.execute("SELECT name FROM sys.database_principals WHERE name = ?", (role,))
            user_role = cursor.fetchone()
            
            if user_role:
                try:
                    # Guardar información en la sesión
                    session['user_role'] = role
                    session['username'] = username
                    session['password'] = password
                    
                    # Ejecutar el procedimiento almacenado
                    cursor.execute("EXEC inicioSesion @Usuario = ?", (username,))
                    conn.commit()
                    
                    cursor.close()
                    conn.close()
                    return redirect(url_for(f'{role}_home'))
                except Exception as e:
                    print(f"Error al registrar inicio de sesión: {str(e)}")
                    cursor.close()
                    conn.close()
                    return render_template('login.html', error_message='Error al registrar inicio de sesión')
            else:
                cursor.close()
                conn.close()
                return render_template('login.html', error_message='Rol seleccionado no válido')
                
        except Exception as e:
            print(f"Error de conexión: {str(e)}")
            return render_template('login.html', error_message='Usuario o contraseña incorrectos')

    return render_template('login.html')

@app.route('/logout')
def logout():
    try:
        if 'username' in session and 'password' in session:
            # Usar las credenciales almacenadas en la sesión
            conn = get_db_connection(session['username'], session['password'])
            cursor = conn.cursor()
            
            # Ejecutar el procedimiento almacenado de cierre de sesión
            cursor.execute("EXEC cerrarSesion @Usuario = ?", session['username'])
            conn.commit()
            
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error al registrar logout: {e}")
    
    session.clear()
    return redirect(url_for('login'))

# Route handlers for different role homepages
@app.route('/admin')
def adminRes_home():
    return render_template('admin_home.html')

@app.route('/camarero')
def camarero_home():
    return render_template('camarero_home.html')

@app.route('/cajero')
def cajero_home():
    return render_template('cajero_home.html')

@app.route('/cocina')
def cocina_home():
    return render_template('cocina_home.html')

if __name__ == '__main__':
    app.run(debug=True)