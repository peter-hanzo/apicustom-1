import subprocess
import uuid
from flask import Flask, request, jsonify, send_file
import os
import ffmpeg
import requests
import psycopg2.binary
import os

DB_HOST = os.environ.get('PGHOST')
DB_PORT = os.environ.get('PGPORT')
DB_USER = os.environ.get('PGUSER')
DB_PASSWORD = os.environ.get('PGPASSWORD')
DB_DATABASE = os.environ.get('PGDATABASE')

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

@app.route('/trim_video_to_mp3', methods=['POST', 'GET'])
def trim_video_to_mp3():
    if request.method == 'POST':
        data = request.form
        video_url = data['video_url']
        start_time = data['start_time']
        end_time = data['end_time']
        audio_bitrate = data.get('audio_bitrate', '128k')
    elif request.method == 'GET':
        video_url = request.args.get('video_url')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        audio_bitrate = request.args.get('audio_bitrate', '128k')

    video_filename = str(uuid.uuid4()) + ".mp4"
    video_filepath = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)

    with open(video_filepath, 'wb') as f:
        response = requests.get(video_url)
        f.write(response.content)

    trimmed_filename = str(uuid.uuid4()) + ".mp3"
    trimmed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], trimmed_filename)

    ffmpeg.input(video_filepath, ss=start_time, to=end_time).output(trimmed_filepath, audio_bitrate=audio_bitrate).run()

    return send_file(trimmed_filepath, as_attachment=True)

@app.route('/add_to_db', methods=['POST'])
def add_to_db():
    data = request.get_json()
    item_name = data['item_name']
    item_description = data['item_description']

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cursor = conn.cursor()

        query = "INSERT INTO items (name, description) VALUES (%s, %s);"
        cursor.execute(query, (item_name, item_description))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success", "message": "Item added to the database successfully."})

    except psycopg2.Error as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run()
