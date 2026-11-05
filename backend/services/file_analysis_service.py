import base64
import io
import mimetypes
from pathlib import Path
from typing import Optional

import pandas as pd
from pypdf import PdfReader

from backend.config import settings
from backend.services.llm_service import llm_service


MAX_FILE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".csv", ".png", ".jpg", ".jpeg", ".webp"}


def analyze_file(filename: str, payload: bytes, prompt: str = "Analyse this file and explain the key findings.") -> str:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Supported files: PDF, CSV, PNG, JPG, JPEG, and WEBP.")
    if len(payload) > MAX_FILE_BYTES:
        raise ValueError("File is too large. Maximum upload size is 10 MB.")
    if not llm_service.client:
        raise RuntimeError("Groq is not configured. Add GROQ_API_KEY before analysing files.")

    if extension == ".pdf":
        reader = PdfReader(io.BytesIO(payload))
        pages = []
        for index, page in enumerate(reader.pages[:40]):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"--- Page {index + 1} ---\n{text}")
        extracted = "\n\n".join(pages)
        if not extracted.strip():
            raise ValueError("No selectable text was found in this PDF. Scanned PDFs need OCR before analysis.")
        if len(extracted) > 60000:
            extracted = extracted[:60000] + "\n[Document text truncated at 60,000 characters.]"
        user_content = (
            f"User request: {prompt}\n\nPDF filename: {filename}\n"
            "Analyse the extracted document text. Cite page numbers when possible, separate facts from inference, "
            "and mention any limitations.\n\n" + extracted
        )
        model = settings.GROQ_MODEL
        response = llm_service.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are TradeMind's document analyst. Be accurate, structured, and transparent about missing information."},
                {"role": "user", "content": user_content}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content or "I couldn't analyse this PDF."

    if extension == ".csv":
        frame = pd.read_csv(io.BytesIO(payload))
        if frame.empty:
            raise ValueError("The CSV file contains no data rows.")
        summary = (
            f"Filename: {filename}\nRows: {len(frame)}\nColumns: {len(frame.columns)}\n"
            f"Column names: {list(frame.columns)}\nData types:\n{frame.dtypes.to_string()}\n"
            f"Missing values:\n{frame.isna().sum().to_string()}\n"
            f"Numeric summary:\n{frame.describe(include='all').to_string()}\n"
            f"Sample rows:\n{frame.head(30).to_csv(index=False)}"
        )
        if len(summary) > 50000:
            summary = summary[:50000] + "\n[CSV summary truncated.]"
        response = llm_service.client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are TradeMind's data analyst. Analyse CSV data carefully. Explain schema, quality issues, patterns, outliers, and actionable findings. Do not invent calculations not supported by the provided summary."},
                {"role": "user", "content": f"User request: {prompt}\n\n{summary}"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content or "I couldn't analyse this CSV."

    mime_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
    encoded = base64.b64encode(payload).decode("ascii")
    response = llm_service.client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": "You are TradeMind's visual analyst. Describe only visible evidence, read charts and tables where legible, distinguish observations from assumptions, and do not invent unreadable values."},
            {"role": "user", "content": [
                {"type": "text", "text": f"{prompt}\nImage filename: {filename}"},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}}
            ]}
        ],
        temperature=0.2,
        max_tokens=1800
    )
    return response.choices[0].message.content or "I couldn't analyse this image."
