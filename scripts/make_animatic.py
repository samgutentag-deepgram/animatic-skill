#!/usr/bin/env python3
"""Render an animatic: one still per beat, narrated by TTS, joined into a 1080p30 mp4.

    python3 make_animatic.py                                   # is there a key? nothing else
    python3 make_animatic.py animatic/beats.json --estimate    # cost, runtime, balance. no render
    python3 make_animatic.py animatic/beats.json               # render
    python3 make_animatic.py animatic/beats.json --voice flux-cole-en --speed 1.2

The beats file format is in BEATS.md. Needs ffmpeg on PATH, Pillow, and DEEPGRAM_API_KEY
in the environment or a .env in the folder you run it from. For another TTS provider, replace tts(): text in, mp3 out.
"""
import argparse, json, os, pathlib, subprocess, sys, tempfile, textwrap, urllib.error, urllib.request
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
BAND = 200                                    # caption band under a still
BREATH = 0.3                                  # air after every line, so cuts aren't clipped
PRICE = 0.045                                 # USD per 1k characters, Flux TTS pay-as-you-go, 2026-09-30
CONSOLE = 'https://console.deepgram.com'


NO_KEY = ('no Deepgram API key found. The narration uses Deepgram TTS, so it needs one.\n'
          f'  1. create a key at {CONSOLE} (new accounts get free credit)\n'
          '  2. put DEEPGRAM_API_KEY=... in a .env in this folder, or export it')


def api_key():
    """The key from the environment, else from ./.env. Never from a parent folder's .env."""
    if os.environ.get('DEEPGRAM_API_KEY'):
        return os.environ['DEEPGRAM_API_KEY']
    env = pathlib.Path.cwd() / '.env'
    if env.is_file():
        for line in env.read_text().splitlines():
            if line.startswith('DEEPGRAM_API_KEY='):
                return line.split('=', 1)[1].strip().strip('"\'') or None
    return None


def tts(text, voice, speed, key):
    """Text in, mp3 bytes out. The only provider-specific function."""
    req = urllib.request.Request(
        f'https://api.deepgram.com/v2/speak?model={voice}&speed={speed}',
        data=json.dumps({'text': text}).encode(),
        headers={'Authorization': f'Token {key}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f'tts failed ({e.code}): {e.read().decode()[:300]}')


def get(path, key):
    req = urllib.request.Request(f'https://api.deepgram.com{path}', headers={'Authorization': f'Token {key}'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def balance(key):
    """Remaining balance in USD, or None with the reason when this key can't read billing."""
    try:
        project = get('/v1/projects', key)['projects'][0]['project_id']
        rows = get(f'/v1/projects/{project}/balances', key)['balances']
    except urllib.error.HTTPError as e:
        why = 'this key has no billing:read scope' if e.code == 403 else f'HTTP {e.code}'
        return None, why
    except (urllib.error.URLError, KeyError, IndexError) as e:
        return None, f'could not read it ({e})'
    return sum(r['amount'] for r in rows if r.get('units', 'usd').lower() == 'usd'), None


def clip_seconds(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                          str(path)], capture_output=True, text=True).stdout
    return float(out or 0)


def estimate(beats, base, price, key):
    """What the render will cost and roughly how long it runs, before any TTS is called."""
    said = [b['say'] for b in beats if b.get('say')]
    chars = sum(len(t) for t in said)
    words = sum(len(t.split()) for t in said)
    sentences = sum(max(1, sum(t.count(p) for p in '.!?')) for t in said)
    played = sum(clip_seconds(base / b['audio']) for b in beats if b.get('audio'))
    secs = words * 0.30 + sentences * 0.70 + played + sum(b.get('hold', 0) + BREATH for b in beats)
    cost = chars / 1000 * price
    print(f'  {len(beats)} beats, {words} words, {chars:,} characters')
    print(f'  about {int(secs // 60)}:{secs % 60:04.1f} of animatic')
    print(f'  about ${cost:.4f} at ${price}/1k characters (--price to change)')
    if not key:
        print(f'  !! {NO_KEY}')
        return
    left, why = balance(key)
    if left is None:
        print(f'  balance unknown: {why}. check it at {CONSOLE}')
    elif left < cost:
        print(f'  !! ${left:.2f} left, not enough for this run. top up at {CONSOLE}')
    else:
        print(f'  ${left:.2f} left, about {int(left / cost) if cost else 0} runs like this one')


def font(size):
    for path in ['/System/Library/Fonts/Helvetica.ttc', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 'C:/Windows/Fonts/arial.ttf']:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def fit(d, text, width_px, height_px, sizes):
    """The largest size whose wrapped text fits the box, and its lines. Ellipsis if none fit."""
    for size in sizes:
        f = font(size)
        chars = max(10, int(width_px / (size * 0.52)))
        lines = textwrap.wrap(text, width=chars)
        if len(lines) * int(size * 1.3) <= height_px:
            return f, size, lines
    keep = max(1, height_px // int(size * 1.3))
    return f, size, lines[:keep - 1] + [textwrap.shorten(' '.join(lines[keep - 1:]), chars, placeholder=' ...')]


def frame(beat, n, total, still, path):
    """A still with the spoken line captioned under it, or a text card when there is no still."""
    img = Image.new('RGB', (W, H), '#111418')
    d = ImageDraw.Draw(img)
    say = beat.get('say') or f'[ {beat["show"]} ]'
    if still:
        pic = Image.open(still).convert('RGB')
        pic.thumbnail((W, H - BAND))
        img.paste(pic, ((W - pic.width) // 2, (H - BAND - pic.height) // 2))
        f, size, lines = fit(d, say, W - 160, BAND - 30, [40, 34, 28, 24])
        y = H - BAND + 15
    else:
        d.text((80, 64), f'{n}/{total}  ·  SHOW: {beat["show"]}', font=font(38), fill='#e0b341')
        f, size, lines = fit(d, say, W - 160, H - 220, [64, 56, 48, 40, 34])
        y = 150 + (H - 220 - len(lines) * int(size * 1.3)) // 2
    for line in lines:
        d.text((80, y), line, font=f, fill='#f1f2f4')
        y += int(size * 1.3)
    img.save(path)


def run(cmd):
    result = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if result.returncode:
        sys.exit(f'ffmpeg failed:\n{result.stderr[-800:]}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('beats', type=pathlib.Path, nargs='?', help='omit to only check for a key')
    ap.add_argument('--voice', default='flux-cole-en')
    ap.add_argument('--speed', type=float, default=1.0, help='0.5 to 1.5. Faster TTS, not a sped-up file')
    ap.add_argument('--out', type=pathlib.Path)
    ap.add_argument('--estimate', action='store_true', help='print cost, runtime and balance, render nothing')
    ap.add_argument('--price', type=float, default=PRICE, help=f'USD per 1k characters (default {PRICE})')
    args = ap.parse_args()
    key = api_key()
    if not args.beats:
        print('key found. ready to render.' if key else NO_KEY)
        sys.exit(0 if key else 1)
    beats = json.loads(args.beats.read_text())
    base = args.beats.parent
    for i, b in enumerate(beats, 1):
        if not (b.get('say') or b.get('audio') or b.get('hold')):
            sys.exit(f'beat {i}: needs "say", "audio" or "hold"')
        for k in ('still', 'audio'):
            if b.get(k) and not (base / b[k]).is_file():
                sys.exit(f'beat {i}: {k} not found: {base / b[k]}')
    out = args.out or args.beats.with_suffix('.mp4')
    if args.estimate:
        estimate(beats, base, args.price, key)
        return
    if not key:
        sys.exit(NO_KEY)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        audio_list, video_list = [], []
        for i, beat in enumerate(beats, 1):
            still = beat.get('still') and base / beat['still']
            if beat.get('audio'):               # a playback: the real clip, not narration
                sound = base / beat['audio']
            elif beat.get('say'):
                sound = tmp / f'{i}.mp3'
                sound.write_bytes(tts(beat['say'], args.voice, args.speed, key))
            else:                               # a silent beat: just the hold
                sound = None
            wav = tmp / f'{i}.wav'
            pad = beat.get('hold', 0) + BREATH
            src = ['-i', sound] if sound else ['-f', 'lavfi', '-t', '0.01', '-i', 'anullsrc=r=48000:cl=mono']
            run(['ffmpeg', '-y', *src, '-af', f'apad=pad_dur={pad}', '-ar', 48000, '-ac', 1, wav])
            frame(beat, i, len(beats), still, tmp / f'{i}.png')
            audio_list.append(f"file '{wav}'\n")
            video_list.append(f"file '{tmp / f'{i}.png'}'\nduration {clip_seconds(wav):.3f}\n")
            print(f'  beat {i}/{len(beats)}  {(beat.get("say") or beat.get("audio") or "(silent) " + beat["show"])[:60]}')
        video_list.append(f"file '{tmp / f'{len(beats)}.png'}'\n")   # concat needs the last frame twice
        (tmp / 'audio.txt').write_text(''.join(audio_list))
        (tmp / 'video.txt').write_text(''.join(video_list))
        # one continuous audio track and one image track, timed from the audio, so nothing drifts
        run(['ffmpeg', '-y', '-f', 'concat', '-safe', 0, '-i', tmp / 'audio.txt', '-c', 'copy', tmp / 'all.wav'])
        run(['ffmpeg', '-y', '-f', 'concat', '-safe', 0, '-i', tmp / 'video.txt', '-i', tmp / 'all.wav',
             '-vf', f'fps={FPS},format=yuv420p', '-c:v', 'libx264', '-tune', 'stillimage',
             '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out])

    secs = clip_seconds(out)
    print(f'wrote {out}  {int(secs // 60)}:{secs % 60:04.1f}  (a floor: you on camera will run longer)')


if __name__ == '__main__':
    main()
