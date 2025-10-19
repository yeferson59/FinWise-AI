from fastapi import APIRouter, UploadFile, HTTPException
from app.services import storage, preprocessing, extraction

router = APIRouter()


@router.post("/extract-text")
async def extract_text(file: UploadFile):
    if file.filename is not None and not file.filename.endswith(
        (".pdf", ".jpg", ".jpeg", ".png", ".gif")
    ):
        raise HTTPException(status_code=400, detail="Invalid file format")

    file_path = await storage.save_file(file)

    preprocessed_path = preprocessing.preprocess_image(file_path)

    raw_text = extraction.extract_text(preprocessed_path)

    return {"raw_text": raw_text}
