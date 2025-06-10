from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import os
import datetime
from enhanced_reproductive_system import EnhancedReproductiveSystem
from reproductive_classification_system import OocyteMaturity

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'  # Ensure upload folder is set

# Initialize enhanced system with AI capabilities
classifier = EnhancedReproductiveSystem(upload_folder=app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('enhanced_index.html')

@app.route('/analyze_sperm', methods=['POST'])
def analyze_sperm():
    try:
        data = request.json
        # Convert string values to appropriate types
        for key in ['concentration', 'progressive_motility', 'normal_morphology', 'volume', 'total_motility', 'vitality', 'ph']:
            if key in data and data[key]:
                data[key] = float(data[key])
        if 'liquefaction_time' in data and data['liquefaction_time']:
            data['liquefaction_time'] = int(data['liquefaction_time'])
            
        result = classifier.classify_sperm(**data)
        return jsonify({
            'success': True,
            'classification': result.classification,
            'sample_id': result.sample_id,
            'details': result.__dict__
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analyze_oocyte', methods=['POST'])
def analyze_oocyte():
    try:
        data = request.json
        data['maturity'] = OocyteMaturity(data['maturity'])
        data['morphology_score'] = int(data['morphology_score'])
        
        result = classifier.classify_oocyte(**data)
        return jsonify({
            'success': True,
            'classification': result.classification,
            'oocyte_id': result.oocyte_id,
            'details': result.__dict__
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analyze_embryo', methods=['POST'])
def analyze_embryo():
    try:
        data = request.json
        # Convert data types
        data['day'] = int(data['day'])
        data['cell_count'] = int(data['cell_count'])
        data['fragmentation'] = float(data['fragmentation'])
        data['multinucleation'] = data['multinucleation'] == 'true'
        
        result = classifier.classify_embryo(**data)
        return jsonify({
            'success': True,
            'classification': result.classification,
            'embryo_id': result.embryo_id,
            'details': result.__dict__
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/report/<analysis_type>/<analysis_id>')
def get_report(analysis_type, analysis_id):
    report = classifier.generate_report(analysis_type, analysis_id)
    return jsonify({'report': report})

@app.route('/analyze_image/<analysis_type>', methods=['POST'])
def analyze_image(analysis_type):
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image file provided'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
    if not classifier.allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)
    try:
        if analysis_type == 'sperm':
            result = classifier.analyze_sperm_with_image(save_path)
        elif analysis_type == 'oocyte':
            result = classifier.analyze_oocyte_with_image(save_path)
        elif analysis_type == 'embryo':
            day = int(request.form.get('day', 3))
            result = classifier.analyze_embryo_with_image(save_path, day)
        else:
            return jsonify({'success': False, 'error': 'Invalid analysis type'}), 400
        result_dict = result.__dict__ if hasattr(result, '__dict__') else dict(result)
        return jsonify({'success': True, 'result': result_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analyze_follicle_scan', methods=['POST'])
def analyze_follicle_scan():
    """AI-enhanced follicle scan analysis"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'})
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        if file and classifier.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"follicle_{timestamp}_{filename}"
            filepath = os.path.join(classifier.upload_folder, filename)
            file.save(filepath)
            # Get additional parameters from form
            form_data = {}
            for key in request.form:
                if request.form[key]:
                    form_data[key] = request.form[key]
            # Analyze with image
            result = classifier.analyze_follicle_scan_with_image(filepath, **form_data)
            return jsonify({
                'success': True,
                'classification': result.classification,
                'scan_id': result.scan_id,
                'image_analysis': getattr(result, 'image_analysis', 'AI analysis completed'),
                'details': result.__dict__
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analyze_hysteroscopy', methods=['POST'])
def analyze_hysteroscopy():
    """AI-enhanced hysteroscopy analysis"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'})
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        if file and classifier.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"hysteroscopy_{timestamp}_{filename}"
            filepath = os.path.join(classifier.upload_folder, filename)
            file.save(filepath)
            # Get additional parameters from form
            form_data = {}
            for key in request.form:
                if request.form[key]:
                    form_data[key] = request.form[key]
            # Analyze with image
            result = classifier.analyze_hysteroscopy_with_image(filepath, **form_data)
            return jsonify({
                'success': True,
                'classification': result.classification,
                'procedure_id': result.procedure_id,
                'image_analysis': getattr(result, 'image_analysis', 'AI analysis completed'),
                'details': result.__dict__
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/ultrasound_report/<analysis_type>/<analysis_id>')
def get_ultrasound_report(analysis_type, analysis_id):
    """Get ultrasound analysis report"""
    try:
        report = classifier.generate_ultrasound_report(analysis_type, analysis_id)
        return jsonify({'report': report})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🚀 Starting AI-Enhanced Reproductive Classification System...")
    print("📸 Image upload and AI analysis features enabled")
    print("🌐 Open your browser and go to: http://localhost:5002")
    app.run(debug=True, host='0.0.0.0', port=5002)
