import collections
import queue
import threading
import time
from typing import Generator

import numpy as np
import pyaudio
import webrtcvad
from faster_whisper import WhisperModel


def realtime_transcriptions(
    *,
    model_name: str = "tiny.en",
    rate: int = 16000,
    frame_ms: int = 30,  # 10/20/30 only
    vad_mode: int = 2,  # 0..3
    end_silence_ms: int = 300,  # pause to end utterance
    padding_ms: int = 300,  # pre-roll
    max_utterance_s: int = 15,  # safety cap
    cpu_threads: int = 8,
) -> Generator[str, None, None]:
    """
    Generator yielding transcribed utterances as strings.
    Stops cleanly when the consumer breaks the loop.

    Example:
        for text in realtime_transcriptions():
            print(text)
    """

    if frame_ms not in (10, 20, 30):
        raise ValueError("frame_ms must be 10, 20, or 30")

    frame_samples = rate * frame_ms // 1000

    audio_q: queue.Queue[bytes] = queue.Queue(maxsize=400)
    stop_evt = threading.Event()

    # Heavy objects created once
    vad = webrtcvad.Vad(vad_mode)
    model = WhisperModel(
        model_name,
        device="cpu",
        compute_type="int8",
        cpu_threads=cpu_threads,
        num_workers=1,
        download_root="./models",
    )

    # Audio capture thread

    def audio_loop():
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=rate,
            input=True,
            frames_per_buffer=frame_samples,
        )
        try:
            while not stop_evt.is_set():
                frame = stream.read(frame_samples, exception_on_overflow=False)
                try:
                    audio_q.put_nowait(frame)
                except queue.Full:
                    # drop oldest to keep latency bounded
                    try:
                        audio_q.get_nowait()
                    except queue.Empty:
                        pass
                    audio_q.put_nowait(frame)
        finally:
            try:
                if stream.is_active():
                    stream.stop_stream()
            except Exception:
                pass
            stream.close()
            p.terminate()

    t_audio = threading.Thread(target=audio_loop, daemon=True)
    t_audio.start()

    # VAD + transcription loop

    ring = collections.deque(maxlen=max(1, padding_ms // frame_ms))
    voiced: list[bytes] = []
    triggered = False
    silence_ms = 0
    utter_start_t: float | None = None

    def reset_transcription() -> None:
        nonlocal triggered, voiced, silence_ms, utter_start_t

        triggered = False
        voiced = []
        ring.clear()
        silence_ms = 0
        utter_start_t = None

    def transcribe(frames: list[bytes]) -> str:
        audio_i16 = np.frombuffer(b"".join(frames), dtype=np.int16)
        audio_f32 = audio_i16.astype(np.float32) / 32768.0

        segments, _ = model.transcribe(
            audio_f32,
            language="en",
            beam_size=1,
            best_of=1,
            temperature=0.0,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return "".join(s.text for s in segments).strip()

    try:
        while True:
            try:
                frame = audio_q.get(timeout=0.1)
            except queue.Empty:
                continue

            is_speech = vad.is_speech(frame, rate)

            if not triggered:
                ring.append(frame)
                if is_speech:
                    triggered = True
                    utter_start_t = time.time()
                    voiced = list(ring)
                    ring.clear()
                    silence_ms = 0
            else:
                voiced.append(frame)

                # safety cap
                if utter_start_t and (time.time() - utter_start_t) > max_utterance_s:
                    text = transcribe(voiced)
                    if text:
                        yield text
                    reset_transcription()
                    continue

                if is_speech:
                    silence_ms = 0
                else:
                    silence_ms += frame_ms
                    if silence_ms >= end_silence_ms:
                        text = transcribe(voiced)
                        if text:
                            yield text
                        reset_transcription()

    finally:
        stop_evt.set()
        t_audio.join(timeout=1.0)
