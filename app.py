from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import os
import json
from detector import detect_code_smells_in_file
from fpdf import FPDF

app = Flask(__name__)

# Set the secret key to sign session data
app.secret_key = 'smell_detector'

UPLOAD_FOLDER = 'uploaded_projects'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan_project():
    # Get the uploaded file from the form
    if 'projectFile' not in request.files:
        return jsonify({"error": "No file selected"}), 400

    project_file = request.files['projectFile']

    if project_file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save the uploaded file temporarily
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], project_file.filename)
    project_file.save(file_path)

    # Store the file path in session (optional)
    session['project_file'] = file_path

    # Define the report path based on the file name
    report_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{os.path.basename(file_path)}_report.json')

    # Run the code smell detector on the file
    detect_code_smells_in_file(file_path, report_path)

    # Load the generated JSON report
    with open(report_path, 'r') as report_file:
        report_data = json.load(report_file)

    return jsonify(report_data)


# Abbreviations for code smells
ABBREVIATIONS = {
    "Long Parameter List": "LPL",
    "Long Scope Chaining": "LSC",
    "Long Message Chain": "LMC",
    "Long Lambda Function ": "LLF",
    "Long Base Class List": "LBCL",

}

@app.route('/download_pdf', methods=['GET'])
def download_pdf():
    # Get project_folder from session
    project_folder = session.get('project_folder')
    
    if not project_folder:
        return jsonify({"error": "Project folder not found in session"}), 400

    report_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{os.path.basename(project_folder)}_report.json')
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{os.path.basename(project_folder)}_report.pdf')

    # Load JSON report data
    try:
        with open(report_path, 'r') as report_file:
            report_data = json.load(report_file)
    except FileNotFoundError:
        return jsonify({"error": "Report not found for the given project folder"}), 404

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Code Smell Detection Report", ln=True, align="C")

    # Add Abbreviations Section
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, "Abbreviations", ln=True)
    pdf.set_font("Arial", "", 12)
    for full_form, abbrev in ABBREVIATIONS.items():
        pdf.cell(200, 8, f"{abbrev} = {full_form}", ln=True)

    # Add Table Header
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Code Smell", 1, 0, "C")
    pdf.cell(110, 10, "File Path", 1, 0, "C")
    pdf.cell(30, 10, "Line No", 1, 1, "C")

    # Add Table Rows
    pdf.set_font("Arial", "", 10)
    for item in report_data:
        # Get the full code smell name and find its abbreviation
        full_code_smell = item["code_smell"]
        code_smell_abbr = ""
        for full_form, abbrev in ABBREVIATIONS.items():
            if full_form in full_code_smell:
                code_smell_abbr = abbrev
                break

        pdf.cell(40, 10, code_smell_abbr, 1, 0, "C")  # Use abbreviation in the cell
        pdf.cell(110, 10, item["file"], 1, 0, "L")
        pdf.cell(30, 10, str(item["line_number"]), 1, 1, "C")

    # Save PDF
    pdf.output(pdf_path)

    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, port=5002)
