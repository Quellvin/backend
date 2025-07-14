from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
DATABASE = 'cars.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                body TEXT,
                fuel TEXT,
                image TEXT
            )
        ''')
        conn.commit()

@app.route('/cars', methods=['GET'])
def get_cars():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM cars')
        cars = [dict(id=row[0], name=row[1], price=row[2], body=row[3], fuel=row[4], image=row[5]) for row in cursor.fetchall()]
        return jsonify(cars)

@app.route('/upload', methods=['POST'])
def upload_car():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected image'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        data = request.form
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cars (name, price, body, fuel, image)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['name'], int(data['price']), data['body'], data['fuel'], filename))
            conn.commit()
        return jsonify({'message': 'Car uploaded successfully'}), 201
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/delete/<int:car_id>', methods=['DELETE'])
def delete_car(car_id):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT image FROM cars WHERE id = ?', (car_id,))
        row = cursor.fetchone()
        if row:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], row[0])
            if os.path.exists(image_path):
                os.remove(image_path)
            cursor.execute('DELETE FROM cars WHERE id = ?', (car_id,))
            conn.commit()
            return jsonify({'message': 'Car deleted'}), 200
        return jsonify({'error': 'Car not found'}), 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)