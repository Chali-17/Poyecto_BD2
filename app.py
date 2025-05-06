from flask import Flask, render_template, request, redirect, url_for, flash, session
import pyodbc

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Database connection configuration
DB_CONFIG = {
    'Driver': '{SQL Server}',
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

        try:
            # Try to establish connection with provided credentials
            conn = get_db_connection(username, password)
            
            # If connection successful, verify if username matches the selected role
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sys.database_principals WHERE name = '{role}'")
            user_role = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if user_role:
                return redirect(url_for(f'{role}_home'))
            else:
                return render_template('login.html', error_message='Rol seleccionado no válido')
                
        except Exception as e:
            return render_template('login.html', error_message='Usuario o contraseña incorrectos')

    return render_template('login.html')

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)