from flask import Flask, request, jsonify, send_from_directory
import trimesh
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ 홈페이지 접속 시 index.html 보여주기!
@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    printer_type = request.form['printer']
    material = request.form['material']

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    mesh = trimesh.load_mesh(filepath)
    volume_cm3 = abs(mesh.volume / 1000)

    material_prices = {
        'PLA': 300,
        'ABS': 400,
        'TPU': 400,
        'PETG': 350,
        '강화레진': 1000,
        '투명레진': 1300
    }

    price_per_cm3 = material_prices.get(material, 200)
    estimate = int(volume_cm3 * price_per_cm3)

    return jsonify({
        "estimate": estimate,
        "volume": round(volume_cm3, 1)
    })

if __name__ == '__main__':
    app.run(debug=True)
