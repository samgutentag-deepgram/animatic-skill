---
name: animatic
description: Build an animatic, a narrated draft of a video the user is about to film, from its script or lesson. Use when the user wants to watch a video before recording it, check its pacing, or plan where the cuts go.
argument-hint: "Which script or lesson should become an animatic?"
---

# Animatic

An animatic is **a draft of the video you can watch before you film it**. Each beat is a still of what the viewer should see, narrated by TTS. It tests the script, so the script's words are the only words in it.

`RENDER` below means `python3 <this skill's folder>/scripts/make_animatic.py`. Run it from the user's project folder.

## First: the key

The narration uses Deepgram TTS. Run `RENDER` with no arguments before anything else. If it says no key was found, stop and walk the user through it:

1. Send them to [console.deepgram.com](https://console.deepgram.com) to sign up (new accounts get free credit, no card) and create an API key.
2. Ask them to come back and paste it.
3. Write `DEEPGRAM_API_KEY=...` to `.env` in the project folder. If the folder is a git repo, add `.env` to its `.gitignore`. Never echo the key back or commit it.

## Steps

1. Read the script or lesson. Cut it into **beats**, one per change in what's on screen.
2. For each beat, `say` is the words spoken aloud, verbatim. If the script has a prompter or spoken-draft section, that's the source; stage directions and markers like `[PLAY]` or `[CUE]` are not, and a marker usually means a new beat. `show` is what the viewer sees, in a few words. Never rewrite `say`: an animatic of your rewrite tests your rewrite.
3. Where the real video plays a sound (a demo, a clip), make it an `audio` beat with the file, so the animatic plays it.
4. Make a **still** for each beat you can. If the script puts a code file on screen and you can read it, render it with `python3 <this skill's folder>/scripts/code_still.py file.py animatic/NN.png --lines 12-20` (the range is lit up). Screenshots and diagrams work too. Where you can't, skip it; a text card showing `show` stands in.
5. Add a `hold` (seconds of silence) wherever the real video goes quiet without a sound file: a command running, a pause to cut on. A beat can be only `show` and `hold`. Guess generously; a short animatic is the usual lie.
6. Write the beats to `animatic/beats.json` in the format in [BEATS.md](BEATS.md), with the stills and clips beside it.
7. **Estimate before you spend:** `RENDER animatic/beats.json --estimate`. Show the user the cost, the rough runtime and their balance. It makes no TTS calls. The balance needs a key with `billing:read`; without it the estimate says so and still prices the run. If it warns the balance is short, stop.
8. Render with `RENDER animatic/beats.json`, then open the mp4 for the user (`open` on macOS, `xdg-open` on Linux).
9. Report the runtime as a **floor**. A person on camera runs longer than TTS.

## Rules

1. **Throwaway.** It lives in `animatic/`, and the mp4 never gets committed. Its job is to be watched once and change the script.
2. **Pacing problems are script problems.** If a beat drags, cut words or split the beat. `--speed` (0.5 to 1.5) makes the voice faster, not the script better.
3. **One beat per shot change.** A beat whose `show` lists two things is two beats, or the still stops matching the words.
