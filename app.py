import subprocess
import uuid
from flask import Flask, request, jsonify, send_file
import os
import ffmpeg
from pytube import YouTube
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

    @app.after_request
    def add_success_message(response):
        response.headers['X-Success-Message'] = 'Video has been successfully trimmed and downloaded.'
        return response

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
        output_format = data.get('output_format', 'mp3')  # Default to mp3
    elif request.method == 'GET':
        video_url = request.args.get('video_url')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        audio_bitrate = request.args.get('audio_bitrate', '128k')
        output_format = request.args.get('output_format', 'mp3')  # Default to mp3

    try:
        # Download the video using pytube
        yt = YouTube(video_url)
        video = yt.streams.filter(progressive=True, file_extension='mp4').first()
        video_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.mp4")
        video.download(output_path=app.config['UPLOAD_FOLDER'], filename=video_filepath)

        trimmed_filename = f"{uuid.uuid4()}.{output_format}"
        trimmed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], trimmed_filename)

        if output_format == 'mp3':
            ffmpeg.input(video_filepath, ss=start_time, to=end_time).output(trimmed_filepath, audio_bitrate=audio_bitrate).run()
        elif output_format == 'mp4':
            ffmpeg.input(video_filepath, ss=start_time, to=end_time).output(trimmed_filepath).run()
        else:
            return jsonify({"status": "error", "message": "Invalid output_format. Supported formats: 'mp3', 'mp4'"})

        os.remove(video_filepath)

        return send_file(trimmed_filepath, as_attachment=True)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
        
@app.route('/add_to_db', methods=['POST', 'GET'])
def add_to_db():
    if request.method == 'POST':
        data = request.get_json()
    elif request.method == 'GET':
        data = request.args

    item_name = data.get('item_name')
    item_description = data.get('item_description')

    if item_name and item_description:
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

            if request.method == 'POST':
                return jsonify({"status": "success", "message": "Item added to the database successfully."})
            elif request.method == 'GET':
                return "Item added to the database successfully."

        except psycopg2.Error as e:
            if request.method == 'POST':
                return jsonify({"status": "error", "message": str(e)})
            elif request.method == 'GET':
                return "Error: " + str(e)

    else:
        if request.method == 'POST':
            return jsonify({"status": "error", "message": "Item name and description must be provided."})
        elif request.method == 'GET':
            return "Error: Item name and description must be provided."

if __name__ == '__main__':
    app.run()
