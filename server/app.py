import os, sys

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "..", "pymodules"))

from flask import Flask, render_template, request, jsonify, make_response
from BrainProcessor import BrainProcessor # change how this is imported
from werkzeug.utils import secure_filename
import numpy as np
from flask_compress import Compress

compress = Compress()

def start_app():
    app = Flask(__name__, static_url_path='/server/static')
    compress.init_app(app)
    return app

app = start_app()

UPLOAD_FOLDER = os.path.join('server','static','uploads')
IMG_FOLDER = os.path.join('server','static','img')
ALLOWED_EXTENSIONS = set(['mha', 'nii'])

brain_processor = BrainProcessor()

@app.route('/')
def landing():
    return render_template("landing.html")


@app.route('/process_mri', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        file = request.files['chooseFile']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            mha_loc = os.path.join(UPLOAD_FOLDER, filename)
            file.save(mha_loc)
            if brain_processor.load_mri(mha_loc):
                brain_data = brain_processor.get_data()
                data_as_list = brain_data['data'].tolist()
                brain = {
                    'data': data_as_list,
                    'dim': list(brain_data['dim']),
                    'filename': filename
                }
                return render_template('brain_info.html', brain=brain)
            else:
                return render_template('landing.html')
            

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/landing')
def index():
    return render_template('landing.html')

@app.route('/applyFilter', methods=['POST'])
def applyFilter():
    
    filter = request.get_json()

    brain_processor.apply_filter(filter)

    result = brain_processor.get_pre_process_output().tolist()
    return jsonify(result)

@app.route('/setPreprocessImage', methods=['POST'])
def setPreprocessImage():

    data = request.get_json()

    view = data['view']
    index = int(data['index'])

    brain_processor.set_view(view)
    brain_processor.set_view_index(index)
    brain_processor.init_pre_process_output()
    
    result = brain_processor.get_original_view().tolist()

    return jsonify(result)

@app.route('/resetPreprocessImage', methods=['POST'])
def resetPreprocessImage():
    print('resetting pre process image')
    brain_processor.init_pre_process_output()
    result = brain_processor.get_pre_process_output().tolist()

    return jsonify(result)

@app.route('/isolateBrain', methods=['POST'])
def isolateBrain():
    print('Isolating brain')
    brain_processor.isolate_brain()
    result = brain_processor.get_pre_process_output().tolist()

    return jsonify(result)

@app.route('/applyWatershed', methods=['POST'])
def applyWatershed():
    print('applying watershed')
    brain_processor.apply_watershed()
    result = brain_processor.get_watershed_output()

    for key in result:
        if not isinstance(result[key], list):
            result[key] = result[key].tolist()

    return jsonify(result)

@app.route('/detectTumor', methods=['POST'])
def detectTumor():
    print('detecting tumor')

    threshold = int(request.get_json())

    result = brain_processor.detect_tumor(threshold)
    result['overlay'] = result['overlay'].tolist()
    result['original'] = result['original'].tolist()
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)