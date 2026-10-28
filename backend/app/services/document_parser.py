import os
from typing import Dict, Any, Tuple
from starlette.concurrency import run_in_threadpool
from app.core.extract import extract_text_from_file
from app.utils.logger import logger


class DocumentParserService:
    def detect_input_type(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        if ext in {".mp3", ".wav", ".m4a"}:
            return "audio"
        elif ext in {".mp4", ".mov", ".avi", ".mkv"}:
            return "video"
        elif ext == ".pdf":
            return "pdf"
        elif ext in {".docx", ".doc"}:
            return "doc"
        elif ext == ".pptx":
            return "pptx"
        elif ext in {".txt", ".md", ".csv", ".json", ".vtt", ".srt"}:
            return "txt"
        return "unstructured_text"

    async def parse_and_normalize(self, file_path: str, filename: str) -> Tuple[str, str, Dict[str, Any]]:
        input_type = self.detect_input_type(filename)
        logger.info(f"[DocumentParser] Parsing file '{filename}' of type '{input_type}' from '{file_path}'")
        
        extracted_text = await run_in_threadpool(extract_text_from_file, file_path)
        normalized_text = extracted_text.strip()
        
        metadata = {
            "filename": filename,
            "input_type": input_type,
            "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "character_count": len(normalized_text),
            "word_count": len(normalized_text.split()),
        }
        
        return normalized_text, input_type, metadata


document_parser = DocumentParserService()
