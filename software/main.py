from realtime_whisper import realtime_transcriptions
from sound_player import (
    play_audio_effect,
    start_crying,
    stop_crying,
)
from constants import (
    WHISPER_PROMPT, 
    VALID_TIME_CMNDS, 
    INSULT_KEYWORDS,
    APOLOGY_KEYWORDS,
    TIME_ERROR_MARGIN,
    INSULT_WINDOW,
)
from utils import (
    clean_speech,
    get_text_after_keyphrase, 
    has_keyphrase,
    parse_time, 
)
from datetime import datetime, date


last_time_cmnd: datetime = datetime.fromtimestamp(0)
is_crying = False


for text in realtime_transcriptions(WHISPER_PROMPT):
    clean_text = clean_speech(text)

    # insult detection
    if has_keyphrase(clean_text, INSULT_KEYWORDS) \
        and not is_crying and datetime.now() - last_time_cmnd < INSULT_WINDOW:
        print("Detected insult & within insult window, crying. Recognized:", clean_text)
        start_crying()
        continue
    
    # apology detection
    if has_keyphrase(clean_text, APOLOGY_KEYWORDS) and is_crying:
        print("Detected apology while crying, stopping. Recognized:", clean_text)
        stop_crying()
        continue

    # time detection
    time_cmnd = get_text_after_keyphrase(clean_text, VALID_TIME_CMNDS)
    if not time_cmnd:
        print("Not valid time command, skipping. Recognized:", clean_text)
        continue

    given_time = parse_time(clean_text)
    if not given_time:
        print("Could not parse given time. Recognized:", clean_text)
        continue

    full_given_time = datetime.combine(date.today(), given_time)
    is_time_correct = abs(datetime.now() - full_given_time) <= TIME_ERROR_MARGIN

    print("Given time:", full_given_time, "is (approx) correct?", is_time_correct)

    last_time_cmnd = datetime.now()
    if is_time_correct:
        play_audio_effect("audio/correct")
    else:
        play_audio_effect("audio/incorrect")

