import subprocess
import uuid
from flask import Flask, request, jsonify, Response, send_file, redirect
import os
import ffmpeg
from pytube import YouTube, Stream
import os
from pydub import AudioSegment

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

def download_youtube_video(video_url):
    return YouTube(video_url)

@app.route('/', methods=['GET'])
def homepage():
    return "Homepage"

@app.route('/hello', methods=['GET'])
def hello():
    return "Hello"

def download_audio(audio_url, audio_format):
    audio_filename = f"{uuid.uuid4()}.{audio_format}"
    audio_filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    
    # Download the audio file
    subprocess.run(["wget", audio_url, "-O", audio_filepath], check=True)
    
    return audio_filepath

def convert_to_mp3(audio_filepath, mp3_bitrate):
    audio_format = audio_filepath.split('.')[-1].lower()
    audio = AudioSegment.from_file(audio_filepath, format=audio_format)
    
    mp3_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.mp3")
    audio.export(mp3_filepath, format="mp3", bitrate=mp3_bitrate)
    
    os.remove(audio_filepath)
    
    return mp3_filepath

def download_clip(video_url):
    return YouTube(f"https://www.youtube.com/{video_url[21:]}")

def trim_video(video_stream: Stream, start_time, end_time):
    video_stream.download(output_path=app.config['UPLOAD_FOLDER'])
    video_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_stream.video_id}.mp4")
    
    trimmed_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.mp4")
    
    ffmpeg.input(video_filepath, ss=start_time, to=end_time).output(trimmed_filepath).run()
    os.remove(video_filepath)
    
    return trimmed_filepath

def download_subtitles(video_url):
    yt = YouTube(video_url)
    transcript = yt.captions.get_by_language_code('en').generate_srt_captions()
    
    subtitles_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.srt")
    
    with open(subtitles_filepath, 'w') as f:
        f.write(transcript)
    
    return subtitles_filepath

@app.route('/download_video', methods=['POST', 'GET'])
def download_video():
    if request.method == 'POST':
        data = request.form
        video_url = data['video_url']
    elif request.method == 'GET':
        video_url = request.args.get('video_url')
    
    try:
        video = download_youtube_video(video_url)
        video_stream = video.streams.filter(progressive=True, file_extension='mp4').first()
        
        return redirect(video_stream.url)  # Redirect to the video stream's URL

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download_audio', methods=['POST', 'GET'])
def download_audio_route():
    if request.method == 'POST':
        data = request.form
        audio_url = data.get('audio_url')
        audio_format = audio_url.split('.')[-1].lower()
        mp3_bitrate = data.get('mp3_bitrate', '128k')
    elif request.method == 'GET':
        audio_url = request.args.get('audio_url')
        audio_format = audio_url.split('.')[-1].lower()
        mp3_bitrate = request.args.get('mp3_bitrate', '128k')

    try:
        if audio_format in ['ogg', 'm4a', 'webm', 'mp3']:
            audio_filepath = download_audio(audio_url, audio_format)
            
            if audio_format != 'mp3':
                mp3_filepath = convert_to_mp3(audio_filepath, mp3_bitrate)
                return send_file(mp3_filepath, as_attachment=True)
            else:
                return send_file(audio_filepath, as_attachment=True)
        else:
            return jsonify({"status": "error", "message": "Invalid audio format. Supported formats: 'ogg', 'm4a', 'webm', 'mp3'"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download_clip', methods=['POST', 'GET'])
def download_clip_route():
    if request.method == 'POST':
        data = request.form
        clip_url = data['clip_url']
    elif request.method == 'GET':
        clip_url = request.args.get('clip_url')

    try:
        clip = download_clip(clip_url)
        video_stream = clip.streams.filter(progressive=True, file_extension='mp4').first()
        
        return send_file(video_stream.url, as_attachment=True)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/trim_video', methods=['POST', 'GET'])
def trim_video_route():
    if request.method == 'POST':
        data = request.form
        video_url = data['video_url']
        start_time = data['start_time']
        end_time = data['end_time']
    elif request.method == 'GET':
        video_url = request.args.get('video_url')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

    try:
        video = download_youtube_video(video_url)
        video_stream = video.streams.filter(progressive=True, file_extension='mp4').first()
        
        trimmed_filepath = trim_video(video_stream, start_time, end_time)
        
        return send_file(trimmed_filepath, as_attachment=True)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/download_subtitles', methods=['GET'])
def download_subtitles():
    video_url = request.args.get('video_url')
    language = request.args.get('language', 'en')  # Default to English if language parameter is not provided

    try:
        yt = YouTube(video_url)
        caption = yt.captions.get_by_language_code(language)
        subtitles = caption.generate_srt_captions()

        return jsonify({"status": "success", "subtitles": subtitles})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run()
