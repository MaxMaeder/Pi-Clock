from datetime import timedelta
from pathlib import Path


def _kw_from_file(file_path: str) -> list[str]:
    base_dir = Path(__file__).resolve().parent

    with open(base_dir / file_path) as f:
        return f.read().split("\n")


WHISPER_PROMPT = """
The speaker is announcing the current time.
Examples:
"It's 12:13."
"It is 1:45."
"It's 9:05."
"It is 10:30."
Times are spoken as hours and minutes and written using H:MM format.
""".strip()


VALID_TIME_CMNDS = ["it is", "its", "time is"]


INSULT_KEYWORDS = _kw_from_file("insults.txt")
INSULT_WINDOW = timedelta(minutes=1)
APOLOGY_KEYWORDS = ["sorry"]


TIME_ERROR_MARGIN = timedelta(minutes=5)
