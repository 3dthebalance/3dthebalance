from flask import Flask, request, jsonify, render_template
import trimesh
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('file')
    printer_type = request.form['printer']
    material = request.form['material']

    allowed_ext = ['.stl', '.obj']
    estimates = []
    total = 0

    material_prices = {
        'PLA': 400,
        'ABS': 500,
        'TPU': 700,
        'PETG': 500,
        '강화레진': 2000,
        '투명레진': 2500
    }

    for file in files:
        filename = file.filename.lower()
        ext = os.path.splitext(filename)[1]
        if ext not in allowed_ext:
            continue

        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        mesh = trimesh.load_mesh(filepath)
        volume_cm3 = abs(mesh.volume / 1000)
        price_per_cm3 = material_prices.get(material, 200)
        estimate = int(round(volume_cm3 * price_per_cm3, -3))
        total += estimate

        estimates.append({
            "filename": filename,
            "volume": round(volume_cm3, 1),
            "estimate": estimate
        })

    return jsonify({
        "estimates": estimates,
        "total": total
    })

if __name__ == '__main__':
    app.run(debug=True)

