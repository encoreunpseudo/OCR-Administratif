import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from ocr_engine import OCREngine
from data_extractor import DataExtractor
from output_manager import OutputManager
import pandas as pd

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tif', 'tiff', 'pdf'}

# Créer les dossiers nécessaires
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Initialiser l'application Flask
app = Flask(__name__)
app.secret_key = "ocr_extraction_super_secret_key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

# Gestionnaire de sortie
output_manager = OutputManager(OUTPUT_FOLDER)

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Gère l'upload de fichier et le traitement OCR"""
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Aucun fichier sélectionné')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Générer un nom de fichier unique
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Récupérer le type de document
        doc_type = request.form.get('document_type', 'ticket')
        
        # Traiter l'image
        try:
            # Initialiser l'OCR et l'extracteur
            ocr = OCREngine()
            extractor = DataExtractor(doc_type)
            
            # Extraire le texte
            text = ocr.extract_text(filepath)
            
            # Extraire les données structurées
            data = extractor.extract_data(text)
            
            # Ajouter le chemin de l'image comme référence
            data['image_src'] = filepath
            
            # Sauvegarder les résultats
            output_format = request.form.get('output_format', 'json')
            
            if output_format == 'csv':
                output_path = output_manager.save_to_csv([data])
            elif output_format == 'excel':
                output_path = output_manager.save_to_excel([data])
            else:
                output_path = output_manager.save_to_json([data])
            
            # Rediriger vers la page de résultats
            return redirect(url_for('result', filepath=filepath, output=output_path))
            
        except Exception as e:
            flash(f'Erreur lors du traitement du fichier: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Type de fichier non autorisé')
    return redirect(url_for('index'))

@app.route('/result')
def result():
    """Affiche les résultats de l'extraction"""
    image_path = request.args.get('filepath', '')
    output_path = request.args.get('output', '')
    
    # Lire les données extraites
    data = {}
    if output_path.endswith('.json'):
        import json
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)[0]  # On prend le premier élément car c'est une liste
    elif output_path.endswith('.csv'):
        df = pd.read_csv(output_path)
        data = df.iloc[0].to_dict()
    elif output_path.endswith('.xlsx'):
        df = pd.read_excel(output_path)
        data = df.iloc[0].to_dict()
    
    # Nom du fichier pour l'affichage
    image_filename = os.path.basename(image_path)
    
    return render_template('results.html', 
                           image_path=image_filename,
                           data=data)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Sert les fichiers uploadés"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/output/<filename>')
def output_file(filename):
    """Sert les fichiers de sortie"""
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/files')
def list_files():
    """Liste tous les fichiers de sortie disponibles"""
    files = output_manager.get_all_outputs()
    return render_template('files.html', files=files)

@app.route('/batch', methods=['GET', 'POST'])
def batch_process():
    """Interface pour le traitement par lot"""
    if request.method == 'POST':
        if 'files[]' not in request.files:
            flash('Aucun fichier sélectionné')
            return redirect(request.url)
        
        files = request.files.getlist('files[]')
        
        if not files or files[0].filename == '':
            flash('Aucun fichier sélectionné')
            return redirect(request.url)
        
        # Récupérer le type de document et le format de sortie
        doc_type = request.form.get('document_type', 'ticket')
        output_format = request.form.get('output_format', 'csv')
        
        # Traiter tous les fichiers
        all_data = []
        processed_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                try:
                    # OCR et extraction
                    ocr = OCREngine()
                    extractor = DataExtractor(doc_type)
                    
                    text = ocr.extract_text(filepath)
                    data = extractor.extract_data(text)
                    data['image_src'] = filepath
                    
                    all_data.append(data)
                    processed_files.append({
                        'filename': file.filename,
                        'status': 'success'
                    })
                except Exception as e:
                    processed_files.append({
                        'filename': file.filename,
                        'status': 'error',
                        'message': str(e)
                    })
        
        # Sauvegarder les résultats si des fichiers ont été traités avec succès
        if all_data:
            timestamp = uuid.uuid4()
            
            if output_format == 'csv':
                output_path = output_manager.save_to_csv(all_data, f'batch_{timestamp}.csv')
            elif output_format == 'excel':
                output_path = output_manager.save_to_excel(all_data, f'batch_{timestamp}.xlsx')
            else:
                output_path = output_manager.save_to_json(all_data, f'batch_{timestamp}.json')
            
            flash(f'{len(all_data)} fichiers traités avec succès. Résultats enregistrés dans {os.path.basename(output_path)}')
        
        return render_template('batch_results.html', files=processed_files, output_path=output_path if all_data else None)
    
    return render_template('batch.html')

@app.route('/api/process', methods=['POST'])
def api_process():
    """API pour le traitement d'un fichier"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        doc_type = request.form.get('document_type', 'ticket')
        
        try:
            ocr = OCREngine()
            extractor = DataExtractor(doc_type)
            
            text = ocr.extract_text(filepath)
            data = extractor.extract_data(text)
            data['image_src'] = filepath
            
            return jsonify({
                'success': True,
                'data': data,
                'text': text
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    app.run(debug=True)