import os
import uuid
from flask import Flask, request, render_template, jsonify, send_from_directory
from zipfile import ZipFile

app = Flask(__name__)

# Set the maximum file size (1000MB in this case)
app.config['MAX_CONTENT_LENGTH'] = 1000 * 1024 * 1024  # 1000MB

# Folder to save the uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Folder to save extracted images
EXTRACTED_IMAGES_FOLDER = 'extracted_images'
if not os.path.exists(EXTRACTED_IMAGES_FOLDER):
    os.makedirs(EXTRACTED_IMAGES_FOLDER)

# Allowed extensions
ALLOWED_EXTENSIONS = {'cbz'}

# Check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to render the upload form
@app.route('/')
def index():
    return render_template('upload.html')

# Route to handle the file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            # Process the uploaded .cbz file
            metadata = process_cbz(filepath, filename)

            return jsonify(metadata)

        except Exception as e:
            # Handle any errors during processing
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500

    return jsonify({"error": "Invalid file format"}), 400

# Function to process .cbz file (extract to a folder named after the uploaded file)
def process_cbz(filepath, filename):
    metadata = {}
    
    # Create a folder named after the uploaded file (without extension)
    folder_name = os.path.splitext(filename)[0]
    extraction_path = os.path.join(EXTRACTED_IMAGES_FOLDER, folder_name)
    os.makedirs(extraction_path, exist_ok=True)

    extracted_files = []  # List to store extracted image filenames
    
    with ZipFile(filepath, 'r') as zip_ref:
        # Extract basic information about the .cbz file
        metadata['file_count'] = len(zip_ref.namelist())  # Number of files in the archive
        metadata['files'] = zip_ref.namelist()  # List of file names in the archive

        # Extract all images to the named folder
        for file in zip_ref.namelist():
            if file.lower().endswith(('jpg', 'jpeg', 'png')):
                zip_ref.extract(file, extraction_path)
                extracted_files.append(os.path.join(folder_name, file))  # Store the relative path to the image

    metadata['extracted_images'] = extracted_files
    return metadata

# Route to serve the extracted images
@app.route('/uploads/images/<folder>/<filename>')
def uploaded_file(folder, filename):
    folder_path = os.path.join(EXTRACTED_IMAGES_FOLDER, folder)
    return send_from_directory(folder_path, filename)

if __name__ == '__main__':
    app.run(debug=True)
