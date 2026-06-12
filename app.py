from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import uuid
import glob
import requests as req

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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

        ydl_opts = {
            "outtmpl": f"{DOWNLOAD_FOLDER}/{filename}.%(ext)s",
            "quiet": True,
            "merge_output_format": "mp4",
            "cookiefile": "cookies.txt",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if info.get("entries"):
                info = info["entries"][0]

            if "url" in info and not info.get("vcodec") or info.get("vcodec") == "none":
                image_url = info.get("url") or info.get("thumbnail")
                ext = "jpg"
                filepath = f"{DOWNLOAD_FOLDER}/{filename}.{ext}"
                headers = {"User-Agent": "Mozilla/5.0"}
                r = req.get(image_url, headers=headers)
                with open(filepath, "wb") as f:
                    f.write(r.content)
                response = send_file(filepath, as_attachment=True, download_name="instagram_photo.jpg")
                os.remove(filepath)
                return response

        if quality == "best":
            format_opt = "bestvideo+bestaudio/best"
        elif quality == "medium":
            format_opt = "bestvideo[height<=480]+bestaudio/best[height<=480]"
        else:
            format_opt = "worstvideo+worstaudio/worst"

        ydl_opts["format"] = format_opt
        with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
            ydl2.extract_info(url, download=True)

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