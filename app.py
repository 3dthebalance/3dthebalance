from flask import Flask, request, jsonify, render_template, send_file
import trimesh
import os
import csv

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    printer_type = request.form['printer']
    material = request.form['material']

    filename = file.filename.lower()
    if not (filename.endswith('.stl') or filename.endswith('.obj')):
        return jsonify({
            "error": "지원하지 않는 파일 형식입니다. STL 또는 OBJ 파일을 업로드해주세요."
        }), 400

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    mesh = trimesh.load_mesh(filepath)
    volume_cm3 = abs(mesh.volume / 1000)  # mm³ → cm³

    material_prices = {
        'PLA': 400,
        'ABS': 500,
        'TPU': 700,
        'PETG': 500,
        '강화레진': 2000,
        '투명레진': 2500
    }

    price_per_cm3 = material_prices.get(material, 200)
    raw_estimate = volume_cm3 * price_per_cm3
    estimate = int(round(raw_estimate, -3))  # 1000원 단위로 반올림

    return jsonify({
        "estimate": estimate,
        "volume": round(volume_cm3, 1)
    })

@app.route('/order', methods=['GET'])
def show_order():
    return render_template('order.html')

@app.route('/order', methods=['POST'])
def submit_order():
    name = request.form['name']
    phone = request.form['phone']
    address = request.form['address']
    estimate = request.form['estimate']
    source = request.form['source']
    custom_source = request.form.get('custom_source', '')

    final_source = custom_source if source == "기타" and custom_source else source

    with open('orders.csv', mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([name, phone, address, estimate, final_source])

    return f"""
    <h2>주문이 완료되었습니다! 감사합니다 :)</h2>
    <p>
      이름: {name}<br>
      연락처: {phone}<br>
      주소: {address}<br>
      견적: {estimate}원<br>
      주문경로: {final_source}
    </p>
    <a href="/">메인으로 돌아가기</a>
    """

@app.route('/orders')
def view_orders():
    return send_file('orders.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)
