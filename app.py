from flask import Flask, request, jsonify, render_template
import trimesh
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ 홈페이지 접속 시 index.html 보여주기
@app.route('/')
def home():
    return render_template('index.html')

# ✅ 견적 계산 처리
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    printer_type = request.form['printer']
    material = request.form['material']

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    mesh = trimesh.load_mesh(filepath)
    volume_cm3 = abs(mesh.volume / 1000)  # mm³ → cm³ (음수 방지)

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

# ✅ 로컬 실행용 (Render에선 무시됨)
if __name__ == '__main__':
    app.run(debug=True)
