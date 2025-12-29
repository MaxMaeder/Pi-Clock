from realtime_whisper import realtime_transcriptions

for text in realtime_transcriptions():
    print("📝", text)
