from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename

from google.cloud import speech
from google.cloud import texttospeech_v1
from google.protobuf import wrappers_pb2
import os

client1=speech.SpeechClient()

def sample_recognize(content):
  audio=speech.RecognitionAudio(content=content)

  config=speech.RecognitionConfig(
  # encoding=speech.RecognitionConfig.AudioEncoding.MP3,
  # sample_rate_hertz=24000,
  language_code="en-US",
  model="latest_long",
  audio_channel_count=1,
  enable_word_confidence=True,
  enable_word_time_offsets=True,
  )

  operation=client1.long_running_recognize(config=config, audio=audio)

  response=operation.result(timeout=90)

  txt = ''
  for result in response.results:
    txt = txt + result.alternatives[0].transcript + '\n'

  return txt

client2 = texttospeech_v1.TextToSpeechClient()

def sample_synthesize_speech(text=None, ssml=None):
    input = texttospeech_v1.SynthesisInput()
    if ssml:
      input.ssml = ssml
    else:
      input.text = text

    voice = texttospeech_v1.VoiceSelectionParams()
    voice.language_code = "en-UK"
    # voice.ssml_gender = "MALE"

    audio_config = texttospeech_v1.AudioConfig()
    audio_config.audio_encoding = "LINEAR16"

    request = texttospeech_v1.SynthesizeSpeechRequest(
        input=input,
        voice=voice,
        audio_config=audio_config,
    )

    response = client2.synthesize_speech(request=request)

    return response.audio_content

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

TEXTUPLOAD_FOLDER = 'textuploads'
ALLOWED_EXTENSIONS = {'wav'}
app.config['TEXTUPLOAD_FOLDER'] = TEXTUPLOAD_FOLDER

os.makedirs(TEXTUPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)
            print(filename)
    files.sort(reverse=True)
    return files

def get_tsfiles():
    files = []
    for filename in os.listdir(TEXTUPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)
            print(filename)
    files.sort(reverse=True)
    return files

@app.route('/')
def index():
    files = get_files()
    tsfiles = get_tsfiles()
    return render_template('index.html', files=files, tsfiles=tsfiles)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        # filename = secure_filename(file.filename)
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        f = open(file_path,'rb')
        data = f.read()
        f.close()

        text = sample_recognize(data)
        f = open(file_path+'.txt','w')
        f.write(text)
        f.close()

    return redirect('/') #success

@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)

    
@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text']
    print(text)
    wav = sample_synthesize_speech(text)
    filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    file_path = os.path.join(app.config['TEXTUPLOAD_FOLDER'], filename)
    
    f = open(file_path,'wb')
    f.write(wav)
    f.close()

    f = open(file_path+'.txt','w')
    f.write(text)
    f.close()

    return redirect('/') #success

@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/textuploads/<filename>')
def textupload_file(filename):
    return send_from_directory(app.config['TEXTUPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)