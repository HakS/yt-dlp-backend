import os
import re
import tempfile
from flask import Flask, request, send_file
import yt_dlp

app = Flask(__name__)

@app.route('/download')
def download():
    url = request.args.get('url')
    if not url:
        return {'error': 'URL parameter is required'}, 400

    ydl_options = process_ytdlp_parameters(request.args)
    print(ydl_options)

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            if 'outtmpl' not in ydl_options:
              ydl_options['outtmpl'] = os.path.join(tmp_dir, '%(title)s.%(ext)s')
            else:
              ydl_options['outtmpl'] = os.path.join(tmp_dir, ydl_options['outtmpl'])

            with yt_dlp.YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(url, download=True)

            downloaded_files = os.listdir(tmp_dir)
            if not downloaded_files:
                return {'error': 'No files were downloaded'}, 500

            file_path = os.path.join(tmp_dir, downloaded_files[0])
            return send_file(
                file_path,
                as_attachment=True,
                download_name=downloaded_files[0]
            )

        except yt_dlp.utils.DownloadError as e:
            return {'error': f'Download failed: {str(e)}'}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


def time_to_seconds(time_str):
    parts = list(map(float, time_str.split(":")))
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return h * 3600 + m * 60 + s

def parse_download_sections(section_str):
    match = re.findall(r'(\d{1,2}:\d{1,2}:\d{1,2})-(\d{1,2}:\d{1,2}:\d{1,2})', section_str)
    return [[time_to_seconds(start), time_to_seconds(end)] for start, end in match]

def process_ytdlp_parameters(args):
    """Convert Flask request parameters to yt-dlp options."""
    options = {}
    print(args.keys())
    for key in args.keys():
        yt_key = key.replace('-', '_')
        if yt_key == 'url':
            continue

        values = args.getlist(key)

        if len(values) == 1 and values[0] == '':
            if yt_key == 'x' or yt_key == 'extract_audio':
                options['format'] = 'bestaudio'
            else:
                options[yt_key] = True
        elif len(values) > 1:
            options[yt_key] = values
        elif values[0].lower() in ('true', 'false'):
            options[yt_key] = values[0].lower() == 'true'
        elif yt_key == 'download_sections':
            options['download_ranges'] =  yt_dlp.utils.download_range_func([], parse_download_sections(values[0]))
        else:
            options[yt_key] = values[0]

    return options

if __name__ == '__main__':
    app.run(debug=True)
