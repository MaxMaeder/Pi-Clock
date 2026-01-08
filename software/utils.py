from datetime import time, datetime


def clean_speech(speech: str) -> str:
    return ''.join(c for c in speech if c.isalnum() or c.isspace()).lower()


def get_text_after_keyphrase(text: str, key_phrases: list[str]) -> str | None:
    for phrase in key_phrases:
        index = text.find(phrase)
        if index != -1:
            return text[index + len(phrase):].lstrip()
    return None


def has_keyphrase(speech: str, key_phrase: list[str]) -> bool:
    return any(cmd in speech for cmd in key_phrase)


def parse_time(speech: str) -> time | None:
    """
    Parse a time from digits found in a string.

    Extracts numerical characters in order and interprets them as a 12-hour
    time. 1-2 digits are treated as an hour, 3-4 digits as hour and minutes.
    AM/PM is inferred from the current system time. Returns None if no valid
    time can be formed.
    """

    # extract digits in order
    digits = [c for c in speech if c.isdigit()]
    n = len(digits)

    if n == 0 or n >= 5:
        return None

    now = datetime.now()
    is_am = now.hour < 12

    try:
        if n <= 2:
            # hour only
            hour = int("".join(digits))
            minute = 0

        else:
            # hours + minutes
            if n == 3:
                hour = int(digits[0])
                minute = int("".join(digits[1:3]))
            else:  # n == 4
                hour = int("".join(digits[0:2]))
                minute = int("".join(digits[2:4]))

        # validate 12-hour clock values
        if not (1 <= hour <= 12):
            return None
        if not (0 <= minute <= 59):
            return None

        # convert to 24-hour time
        if is_am:
            hour_24 = 0 if hour == 12 else hour
        else:
            hour_24 = 12 if hour == 12 else hour + 12

        return time(hour=hour_24, minute=minute)

    except ValueError:
        return None
