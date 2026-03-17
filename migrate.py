import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Actualize Plan
content = content.replace(
    "@app.route('/actualize-plan', methods=['GET'])\ndef actualize_plan():\n    return render_template('actualize.html')",
    "# @app.route('/actualize-plan', methods=['GET'])\n# def actualize_plan():\n#     return render_template('actualize.html')\n\n@app.route('/api/actualize-plan', methods=['GET'])\ndef api_actualize_plan():\n    return jsonify({'message': 'Actualize plan page data'})"
)

# 2. Backup Networks
content = content.replace(
    "@app.route('/backup-networks', methods=['GET'])\ndef backup_networks():\n    return render_template('backup.html')",
    "# @app.route('/backup-networks', methods=['GET'])\n# def backup_networks():\n#     return render_template('backup.html')\n\n@app.route('/api/backup-networks', methods=['GET'])\ndef api_backup_networks():\n    return jsonify({'message': 'Backup networks page data'})"
)

# 3. Upload CSV logic
old_upload_csv_start = """@app.route('/upload-csv', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'GET':
        return render_template('upload.html')
    else:"""

new_upload_csv_start = """# @app.route('/upload-csv', methods=['GET', 'POST'])
# def upload_csv():
#     if request.method == 'GET':
#         return render_template('upload.html')
#     else:

@app.route('/api/upload-csv', methods=['POST'])
def api_upload_csv_real():
    if True:"""

content = content.replace(old_upload_csv_start, new_upload_csv_start)

# 4. Remove the dummy api_upload_csv block
dummy_api_upload = """@app.route('/api/upload-csv', methods=['GET'])
def api_upload_csv():
    return jsonify({"message": "Upload CSV page data", "endpoint": "/api/upload-csv"})"""

content = content.replace(dummy_api_upload, "")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Migration successful")
