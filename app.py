from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import os
from audio_processor import AudioProcessor

app = Flask(__name__)
app.secret_key = '123#awerqfa'  # For session management

# Path for uploaded files
UPLOAD_FOLDER = 'static/upload_files'
ALLOWED_EXTENSIONS={'wav','mp3','flac','ogg'}
audio_file_path=None
processor=AudioProcessor()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Audio Processor object
audio_processor = AudioProcessor()

@app.route('/')
def index():
    if 'step' not in session:
        session['step'] = 1
    return render_template('index.html', step=session.get('step'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        session['file_path'] = file_path
        return redirect(url_for('index'))

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file_path' in session:
        audio_path = session['file_path']
        audio_processor.transcribe(audio_path)
        return redirect(url_for('result'))
    return redirect(url_for('index'))

@app.route('/diarize', methods=['POST'])
def diarize():
    if 'file_path' in session:
        audio_path = session['file_path']
        audio_processor.diarize(audio_path)
        return redirect(url_for('result'))
    return redirect(url_for('index'))

@app.route('/extract_features', methods=['POST'])
def extract_features():
    if 'file_path' in session:
        audio_path = session['file_path']
        audio_processor.extract_features(audio_path)
        return redirect(url_for('result'))
    return redirect(url_for('index'))

@app.route('/result')
def result():
    if 'file_path' in session:
        transcription = audio_processor.transcription
        diarization = audio_processor.diarization
        features = audio_processor.features
        return render_template('result.html', transcription=transcription, diarization=diarization, features=features)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()  # Clear session
    return redirect(url_for('index'))

@app.route('/process_new_file')
def process_new_file():
    audio_processor.__init__()  # Reset the AudioProcessor object
    session.clear()  # Clear session
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
