import subprocess
import uuid
from flask import Flask, request, jsonify, send_file
import os
import ffmpeg
import requests
from werkzeug.utils import secure_filename
from scipy.spatial import distance

def create_app():
    app = Flask(__name__, static_folder='uploads', static_url_path='/uploads')
    app.config['UPLOAD_FOLDER'] = '/app/uploads/'
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return app

app = create_app()

@app.route('/', methods=['GET'])
def homepage():
    return "Homepage"

@app.route('/hello', methods=['GET'])
def hello():
    return "Hello"

@app.route('/trim_video_to_mp3', methods=['POST'])
def trim_video_to_mp3():
    data = request.form
    video_url = data['video_url']
    start_time = data['start_time']
    end_time = data['end_time']

    video_filename = str(uuid.uuid4()) + ".mp4"
    video_filepath = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)

    with open(video_filepath, 'wb') as f:
        response = requests.get(video_url)
        f.write(response.content)

    trimmed_filename = str(uuid.uuid4()) + ".mp3"
    trimmed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], trimmed_filename)

    ffmpeg.input(video_filepath, ss=start_time, t=end_time).output(trimmed_filepath).run()

    return send_file(trimmed_filepath, as_attachment=True)

if __name__ == '__main__':
    app.run()
