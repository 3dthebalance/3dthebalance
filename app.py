from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import datetime
import json
import trimesh

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Google API 설정
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

# 환경변수에서 service_account 정보 불러오기
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=creds)
sheet_service = build('sheets', 'v4', credentials=creds)

SPREADSHEET_ID = "1KmlihVAwcQagX48iG5y-GDnCoMaMpHovLMeiZJqFGPk"
DRIVE_FOLDER_ID = "1djicleZgTLhtMViaFbARlc8r_bQ6ULIe"

# 대표님 요청 기준 단가 설정 (원/cm^3)
material_prices = {
    'PLA': 170,
    'ABS': 200,
    'TPU': 210,
    'PETG': 200,
    '강화레진': 350,
    '투명레진': 380
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('file')
    printer_type = request.form['printer']
    material = request.form['material']

    allowed_ext = ['.stl', '.obj']
    seen_filenames = set()
    estimates = []
    total = 0

    for file in files:
        filename = file.filename.lower()
        ext = os.path.splitext(filename)[1]
        if ext not in allowed_ext:
            continue

        if filename in seen_filenames:
            continue
        seen_filenames.add(filename)

        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            mesh = trimesh.load_mesh(filepath)
            volume_cm3 = abs(mesh.volume / 1000)
            bounds = mesh.bounds
            x = round(bounds[1][0] - bounds[0][0], 1)
            y = round(bounds[1][1] - bounds[0][1], 1)
            z = round(bounds[1][2] - bounds[0][2], 1)
        except:
            volume_cm3 = 0
            x = y = z = 0

        price_per_cm3 = material_prices.get(material, 200)
        estimate = int(round(volume_cm3 * price_per_cm3, -3))
        total += estimate

        estimates.append({
            "filename": filename,
            "volume": round(volume_cm3, 1),
            "x": x,
            "y": y,
            "z": z,
            "estimate": estimate
        })

    return jsonify({
        "estimates": estimates,
        "total": total
    })

@app.route('/order')
def order():
    estimate = request.args.get('estimate', '0')
    return render_template('order.html', estimate=estimate)

def upload_file_to_drive(file_path, filename):
    file_metadata = {
        'name': filename,
        'parents': [DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(file_path, mimetype='application/octet-stream')
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    drive_service.permissions().create(
        fileId=uploaded_file['id'],
        body={'type': 'anyone', 'role': 'reader'},
    ).execute()

    return f"https://drive.google.com/file/d/{uploaded_file['id']}/view?usp=sharing"

def record_order_to_sheet(name, phone, address, estimate, channel, file_links):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for fname, link in file_links:
        row = [now, name, phone, address, estimate, channel, fname, link]
        sheet_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="A1",
            valueInputOption="RAW",
            body={"values": [row]}
        ).execute()

@app.route('/submit-order', methods=['POST'])
def submit_order():
    name = request.form['name']
    phone = request.form['phone']
    address = request.form['address']
    estimate = request.form['estimate']
    channel = request.form['channel']
    channel_detail = request.form.get('channel_detail', '')

    full_channel = channel if channel != '기타' else f"기타: {channel_detail}"

    uploaded_files = request.files.getlist("file")
    file_links = []

    for file in uploaded_files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        link = upload_file_to_drive(file_path, filename)
        file_links.append((filename, link))

    record_order_to_sheet(name, phone, address, estimate, full_channel, file_links)

    return "주문이 정상적으로 접수되었습니다. 감사합니다!"

if __name__ == '__main__':
    app.run(debug=True)

