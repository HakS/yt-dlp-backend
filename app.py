import os
import re
import json
import glob
import tempfile
import subprocess
from flask import Flask, request, send_file
import yt_dlp

app = Flask(__name__)

INSTAGRAM_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# ffmpeg directory (Homebrew default); also used by yt-dlp's video conversion
# path. Override with the FFMPEG_DIR env var if ffmpeg lives elsewhere.
FFMPEG_DIR = os.environ.get('FFMPEG_DIR', '/opt/homebrew/bin')
FFMPEG_LOCATION = os.path.join(FFMPEG_DIR, 'ffmpeg')

# whisperx is NOT installed in this app's venv. It lives in a separate pyenv
# (Python 3.11.13 + torch). We invoke it out-of-process against that interpreter
# so the Flask venv stays light and we reuse the working torch install.
# Set WHISPERX_PYTHON to the absolute path of that interpreter (see README).
WHISPERX_PYTHON = os.environ.get('WHISPERX_PYTHON', 'python3')

# whisperx on this Mac runs on CPU (CUDA unavailable). The 'small' model is the
# default speed/accuracy tradeoff; larger models are much slower on CPU.
WHISPERX_TIMEOUT = 1800  # seconds


def is_instagram_url(url):
    return 'instagram.com' in (url or '').lower()


def apply_instagram_defaults(options, url):
    # Age-gated posts (e.g. alcohol) require a real browser UA + referer + a
    # logged-in session. Pulling cookies from Chrome covers the auth side.
    if not is_instagram_url(url):
        return
    headers = options.setdefault('http_headers', {})
    headers.setdefault('User-Agent', INSTAGRAM_USER_AGENT)
    headers.setdefault('Referer', 'https://www.instagram.com/')
    options.setdefault('cookiesfrombrowser', ('chrome',))


def find_downloaded_file(info, tmp_dir):
    """Robustly resolve the path of the file yt-dlp just downloaded.

    Prefers the path reported in yt-dlp's metadata, falling back to a directory
    listing (ignoring hidden files like .DS_Store). Returns None if nothing was
    downloaded.
    """
    if 'requested_downloads' in info and len(info['requested_downloads']) > 0:
        return info['requested_downloads'][0]['filepath']
    downloaded_files = [f for f in os.listdir(tmp_dir) if not f.startswith('.')]
    if not downloaded_files:
        return None
    return os.path.join(tmp_dir, downloaded_files[0])


@app.route('/download')
def download():
    url = request.args.get('url')
    if not url:
        return {'error': 'URL parameter is required'}, 400

    ydl_options = process_ytdlp_parameters(request.args)
    apply_instagram_defaults(ydl_options, url)
    print(ydl_options)

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            if 'outtmpl' not in ydl_options:
                ydl_options['outtmpl'] = os.path.join(tmp_dir, '%(title).16s.%(ext)s')
            else:
                ydl_options['outtmpl'] = os.path.join(tmp_dir, ydl_options['outtmpl'])

            with yt_dlp.YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = find_downloaded_file(info, tmp_dir)
                if not file_path:
                    return {'error': 'No files were downloaded'}, 500

            filename = os.path.basename(file_path)
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename
            )

        except yt_dlp.utils.DownloadError as e:
            return {'error': f'Download failed: {str(e)}'}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


class WhisperxError(Exception):
    """Raised when the whisperx subprocess fails or produces no output."""


def download_audio(url, tmp_dir, args):
    """Download ONLY the audio for `url` into tmp_dir and return its file path.

    Unlike /download this deliberately avoids process_ytdlp_parameters (which
    forces the H.265 video-conversion path); it grabs bestaudio and extracts it
    to a single mp3 via ffmpeg, which whisperx then transcribes.
    """
    ydl_options = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(tmp_dir, 'audio.%(ext)s'),
        'ffmpeg_location': FFMPEG_LOCATION,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
        'noprogress': True,
    }

    # Reuse the same auth handling as /download for gated sources.
    apply_instagram_defaults(ydl_options, url)
    cookies = args.get('cookies_from_browser') or args.get('cookies-from-browser')
    if cookies:
        ydl_options['cookiesfrombrowser'] = parse_cookies_from_browser(cookies)

    with yt_dlp.YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = find_downloaded_file(info, tmp_dir)

    if not file_path or not os.path.exists(file_path):
        # The ExtractAudio postprocessor rewrites the extension; the metadata
        # path may point at the pre-conversion file, so fall back to the mp3.
        mp3s = glob.glob(os.path.join(tmp_dir, '*.mp3'))
        if mp3s:
            return mp3s[0]
        raise WhisperxError('No audio was downloaded')
    return file_path


def run_whisperx(audio_path, out_dir, model, language, task, align):
    """Run whisperx out-of-process and return its parsed JSON output."""
    cmd = [
        WHISPERX_PYTHON, '-m', 'whisperx', audio_path,
        '-o', out_dir,
        '-f', 'json',
        '--device', 'cpu',
        '--model', model,
        '--task', task,
        '--log-level', 'error',
    ]
    if language:
        cmd += ['--language', language]
    if not align:
        cmd.append('--no_align')

    # Ensure whisperx finds ffmpeg even if the server's PATH is minimal.
    env = dict(os.environ)
    env['PATH'] = FFMPEG_DIR + os.pathsep + env.get('PATH', '')

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=WHISPERX_TIMEOUT, env=env,
        )
    except subprocess.TimeoutExpired:
        raise WhisperxError(f'whisperx timed out after {WHISPERX_TIMEOUT}s')

    if proc.returncode != 0:
        raise WhisperxError(f'whisperx failed: {proc.stderr.strip()[-2000:]}')

    json_files = glob.glob(os.path.join(out_dir, '*.json'))
    if not json_files:
        raise WhisperxError('whisperx produced no JSON output')
    with open(json_files[0]) as f:
        return json.load(f)


def shape_response(raw, fmt):
    """Reduce whisperx's raw output to the requested token-cheap shape."""
    segments = raw.get('segments', [])
    full_text = ' '.join(s.get('text', '').strip() for s in segments).strip()
    language = raw.get('language')

    if fmt == 'text':
        return {'language': language, 'text': full_text}

    if fmt == 'full':
        return raw

    # Default: segment-level timestamps + full text, dropping word-level data.
    duration = segments[-1].get('end') if segments else 0
    return {
        'language': language,
        'duration': duration,
        'text': full_text,
        'segments': [
            {
                'start': s.get('start'),
                'end': s.get('end'),
                'text': s.get('text', '').strip(),
            }
            for s in segments
        ],
    }


@app.route('/transcribe')
def transcribe():
    url = request.args.get('url')
    if not url:
        return {'error': 'URL parameter is required'}, 400

    fmt = request.args.get('response_format', 'segments')
    if fmt not in ('segments', 'text', 'full'):
        return {'error': "response_format must be 'segments', 'text', or 'full'"}, 400

    model = request.args.get('model', 'small')
    language = request.args.get('language')  # None => auto-detect
    task = request.args.get('task', 'transcribe')
    # Word-level alignment is only needed for the verbose 'full' format.
    align = fmt == 'full'

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            audio_path = download_audio(url, tmp_dir, request.args)
            raw = run_whisperx(audio_path, tmp_dir, model, language, task, align)
            return shape_response(raw, fmt)
        except yt_dlp.utils.DownloadError as e:
            return {'error': f'Download failed: {str(e)}'}, 500
        except WhisperxError as e:
            return {'error': str(e)}, 500
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

def parse_cookies_from_browser(spec):
    """Convert the CLI cookies spec to yt-dlp's Python-API tuple.

    CLI flag form: BROWSER[+KEYRING][:PROFILE][::CONTAINER]
    Python API expects (browser, profile, keyring, container).
    """
    container = None
    if '::' in spec:
        spec, container = spec.split('::', 1)
    profile = None
    if ':' in spec:
        spec, profile = spec.split(':', 1)
    keyring = None
    if '+' in spec:
        spec, keyring = spec.split('+', 1)
    return (spec, profile, keyring, container)

def process_ytdlp_parameters(args):
    """Convert Flask request parameters to yt-dlp options."""
    options = {}
    
    for key in args.keys():
        yt_key = key.replace('-', '_')
        if yt_key == 'url':
            continue

        values = args.getlist(key)

        if len(values) == 1 and values[0] == '':
            if yt_key in ('x', 'extract_audio'):
                options['format'] = 'bestaudio'
            else:
                options[yt_key] = True
        elif len(values) > 1:
            options[yt_key] = values
        elif values[0].lower() in ('true', 'false'):
            options[yt_key] = values[0].lower() == 'true'
        elif yt_key == 'download_sections':
            options['download_ranges'] =  yt_dlp.utils.download_range_func([], parse_download_sections(values[0]))
        elif yt_key == 'cookies_from_browser':
            options['cookiesfrombrowser'] = parse_cookies_from_browser(values[0])
        else:
            options[yt_key] = values[0]

    # Always apply Apple compatibility fix for video downloads (personal Mac tool)
    if options.get('format') != 'bestaudio':
        # These flags mirror the user's manual fix command for QuickTime/macOS compatibility:
        # -tag:v hvc1: Essential for Apple devices to play HEVC (H.265) videos in MP4
        # -pix_fmt yuv420p: Standard color format for universal playback
        # -movflags +faststart: Optimized for web playback and quick previews
        ffmpeg_args = ['-c:v', 'libx265', '-tag:v', 'hvc1', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart']
        
        options.setdefault('postprocessor_args', {}).update({
            'ffmpeg': ffmpeg_args,
            'video-convertor': ffmpeg_args
        })
        options['merge_output_format'] = 'mp4'
        options['ffmpeg_location'] = FFMPEG_LOCATION
        
        # Ensure conversion happens even if the source is already in a single stream
        if not any(pp.get('key') == 'FFmpegVideoConvertor' for pp in options.get('postprocessors', [])):
            options.setdefault('postprocessors', []).append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            })

    return options

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
