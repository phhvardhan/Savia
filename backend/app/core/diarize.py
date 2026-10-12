
from app.core.config import settings
from app.utils.logger import logger

_diarization_pipeline = None
_diarization_unavailable = False


def get_diarization_pipeline():
    global _diarization_pipeline, _diarization_unavailable

    if _diarization_unavailable:
        return None

    if _diarization_pipeline is None:
        if not settings.HF_TOKEN:
            logger.warning("HF_TOKEN not set — diarization disabled, all speakers will be 'UNKNOWN'.")
            _diarization_unavailable = True
            return None

        try:
            from pyannote.audio import Pipeline
            logger.info("Loading pyannote speaker-diarization pipeline...")
            _diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=settings.HF_TOKEN,
            )
            logger.info("Diarization pipeline ready.")
        except Exception as e:
            logger.warning(f"Failed to load diarization pipeline, disabling diarization: {e}")
            _diarization_unavailable = True
            return None

    return _diarization_pipeline


def diarize_audio(wav_path: str) -> list[dict]:
    pipeline = get_diarization_pipeline()

    if pipeline is None:
        logger.info("Diarization unavailable — skipping, will fall back to UNKNOWN speaker.")
        return []

    logger.info(f"Running diarization on {wav_path}...")
    diarization = pipeline(wav_path)

    result = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        result.append({
            "speaker": speaker,
            "start": turn.start,
            "end": turn.end,
        })
    return result