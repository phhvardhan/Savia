def merge_diarization_and_transcript(
    diarization_segments: list[dict],
    transcript_segments: list[dict],
) -> list[dict]:
    """
    diarization_segments: [{"speaker": "SPEAKER_00", "start": 0.0, "end": 4.8}, ...]
    transcript_segments:  [{"start": 0.0, "end": 4.8, "text": "Okay let's start"}, ...]
    """
    merged = []

    for t_seg in transcript_segments:
        t_start, t_end = t_seg["start"], t_seg["end"]
        best_speaker = "UNKNOWN"
        best_overlap = 0.0

        for d_seg in diarization_segments:
            overlap_start = max(t_start, d_seg["start"])
            overlap_end = min(t_end, d_seg["end"])
            overlap = max(0.0, overlap_end - overlap_start)

            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = d_seg["speaker"]

        merged.append({
            "speaker_name": best_speaker,
            "speaker": best_speaker,
            "start_seconds": t_start,
            "end_seconds": t_end,
            "text": t_seg["text"],
        })

    return merged