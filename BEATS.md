# Beats format

A JSON list, one object per beat, in running order. Paths are relative to `beats.json`.

```json
[
  {"show": "terminal, the prompt typed out", "say": "here's the whole idea in one prompt.", "still": "01-prompt.png"},
  {"show": "the demo clip playing", "audio": "demo.wav"},
  {"show": "the command running", "say": "watch what comes back.", "hold": 3},
  {"show": "terminal, output scrolling", "hold": 4},
  {"show": "to camera", "say": "so that's the shape of it."}
]
```

| Key | Meaning |
|---|---|
| `say` | The spoken line, verbatim from the script. Narrated by TTS |
| `audio` | A sound file to play instead of narration: a demo, a clip |
| `show` | Required. What the viewer sees. On screen when there's no still |
| `still` | An image shown for the beat, with `say` captioned underneath |
| `hold` | Seconds of silence after the beat. Default 0. A beat needs `say`, `audio` or `hold` |
