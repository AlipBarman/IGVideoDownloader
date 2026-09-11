from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import uuid
import glob
import requests as req
import imageio_ffmpeg

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    quality = data.get("quality", "best")
    if not url:
        return jsonify({"error": "URL required"}), 400
    try:
        filename = str(uuid.uuid4())

        if quality == "best":
            format_opt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        elif quality == "medium":
            format_opt = "bestvideo[height<=480]+bestaudio/best[height<=480]/best"
        else:
            format_opt = "worstvideo+worstaudio/worst"

        ydl_opts = {
            "outtmpl": f"{DOWNLOAD_FOLDER}/{filename}.%(ext)s",
            "quiet": True,
            "format": format_opt,
            "cookiefile": "www.instagram.com_cookies.txt",
            "ffmpeg_location": ffmpeg_path,
            "merge_output_format": "mp4",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        files = glob.glob(f"{DOWNLOAD_FOLDER}/{filename}.*")
        if not files:
            return jsonify({"error": "Could not download"}), 500

        filepath = files[0]
        response = send_file(filepath, as_attachment=True)
        os.remove(filepath)
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)