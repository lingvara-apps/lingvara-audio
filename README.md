# Lingvara Audio

Haydi Rusça uygulamasının kayıtlı ses paketleri (A2–C2). Her ünite `packs/SEVİYE-NN.zip`.

## Other courses (es, de, fr, it, pt, ja, ko, zh, tr, ar)

Not stored in the repo: each course is published as GitHub Release `audio-<course>`
(`manifest.json` + `<course>-<LEVEL>-<NN>.zip`, layout per the app's docs/AUDIO-LAYOUT.md).

- Run: Actions → **tts-multi** → Run workflow → `course` = es / de / … Text comes from `course_<c>/` on branch `tr-gemini`.
  Re-runs only synthesize keys that have no clip in the current release (tick `force` after changing voices/text rules).
- Engines and voices: `tts/langs.json` (Kokoro: es fr it pt ja zh; Supertonic: de tr ar ko and the French male voice).
  Male dialog speakers: `male_names` (unknown speaker names are printed by `tts/extract.py`).
- Voice auditions: Actions → **tts-samples** → release `audio-samples` (`report.txt` has Whisper CER per voice).
