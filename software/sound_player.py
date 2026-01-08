import random
import pygame
from pathlib import Path


pygame.mixer.init()


_base_dir = Path(__file__).resolve().parent


def play_audio_effect(folder: str) -> None:
    sound_dir = _base_dir / folder

    files = list(sound_dir.iterdir())

    sound_path = random.choice(files)

    sound = pygame.mixer.Sound(sound_path)
    sound.play()


_crying_sound = pygame.mixer.Sound(str(_base_dir / "audio" / "crying.wav"))


def start_crying() -> None:
    _crying_sound.play(loops=-1)


def stop_crying() -> None:
    _crying_sound.stop()
