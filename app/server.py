import os
from flask import Flask, render_template, send_from_directory, request, Response

app = Flask(__name__, template_folder='templates', static_folder='static')

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(STATIC_DIR, 'manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory(STATIC_DIR, 'sw.js', mimetype='application/javascript')

@app.route('/api/videos')
def get_videos():
    json_path = os.path.join(DATA_DIR, 'videos.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            return Response(f.read(), mimetype='application/json')
    return Response('{"videos":[]}', mimetype='application/json')

# Video streaming with HTTP Range support for iOS/Android scrub & smooth playback
@app.route('/video/<path:filename>')
@app.route('/static/<path:filename>')
def serve_static_or_video(filename):
    file_path = os.path.join(STATIC_DIR, filename)
    dir_to_serve = STATIC_DIR
    if not os.path.exists(file_path):
        root_static = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', filename)
        if os.path.exists(root_static):
            file_path = root_static
            dir_to_serve = os.path.dirname(root_static)
        else:
            return "File not found", 404

    # Standard non-video files
    if not filename.endswith('.mp4'):
        return send_from_directory(dir_to_serve, filename)

    # Range request handling for smooth mobile video streaming
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)

    if not range_header:
        return send_from_directory(dir_to_serve, filename, mimetype='video/mp4')

    byte1, byte2 = 0, None
    m = range_header.replace('bytes=', '').split('-')
    if m[0]:
        byte1 = int(m[0])
    if len(m) > 1 and m[1]:
        byte2 = int(m[1])

    length = file_size - byte1
    if byte2 is not None:
        length = byte2 - byte1 + 1

    with open(file_path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    rv = Response(data, 206, mimetype='video/mp4', content_type='video/mp4', direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {byte1}-{byte1 + len(data) - 1}/{file_size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    return rv

if __name__ == '__main__':
    print("🚀 CinePulse Mobile Studio Hub launching on port 5050...")
    print("📱 Local network access: http://192.168.1.40:5050")
    app.run(host='0.0.0.0', port=5050, debug=False)
