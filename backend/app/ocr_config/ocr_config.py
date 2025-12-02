"""
OCR Configuration Module
Contains different presets for OCR processing based on document type.
"""

from enum import Enum
from typing import Any


class PSMMode(Enum):
    """Tesseract Page Segmentation Modes"""

    OSD_ONLY = 0  # Orientation and script detection only
    AUTO_OSD = 1  # Automatic page segmentation with OSD
    AUTO_ONLY = 2  # Automatic page segmentation, but no OSD
    AUTO = 3  # Fully automatic page segmentation, but no OSD (Default)
    SINGLE_COLUMN = 4  # Assume a single column of text of variable sizes
    SINGLE_BLOCK_VERT_TEXT = (
        5  # Assume a single uniform block of vertically aligned text
    )
    SINGLE_BLOCK = 6  # Assume a single uniform block of text
    SINGLE_LINE = 7  # Treat the image as a single text line
    SINGLE_WORD = 8  # Treat the image as a single word
    CIRCLE_WORD = 9  # Treat the image as a single word in a circle
    SINGLE_CHAR = 10  # Treat the image as a single character
    SPARSE_TEXT = (
        11  # Sparse text. Find as much text as possible in no particular order
    )
    SPARSE_TEXT_OSD = 12  # Sparse text with OSD
    RAW_LINE = 13  # Raw line. Treat the image as a single text line


class OEMMode(Enum):
    """Tesseract OCR Engine Modes"""

    LEGACY = 0  # Legacy engine only
    NEURAL_NET = 1  # Neural nets LSTM engine only
    LEGACY_LSTM = 2  # Legacy + LSTM engines
    DEFAULT = 3  # Default, based on what is available


class DocumentType(Enum):
    """Types of documents for optimized OCR processing"""

    RECEIPT = "receipt"
    INVOICE = "invoice"
    DOCUMENT = "document"
    FORM = "form"
    HANDWRITTEN = "handwritten"
    SCREENSHOT = "screenshot"
    PHOTO = "photo"
    GENERAL = "general"


class OCRConfig:
    """Base OCR Configuration"""

    def __init__(
        self,
        psm_mode: PSMMode = PSMMode.AUTO,
        oem_mode: OEMMode = OEMMode.DEFAULT,
        language: str = "eng+spa",  # Support both English and Spanish by default
        preserve_interword_spaces: bool = True,
        additional_params: dict[str, Any] | None = None,
    ):
        self.psm_mode: PSMMode = psm_mode
        self.oem_mode: OEMMode = oem_mode
        self.language: str = language
        self.preserve_interword_spaces: bool = preserve_interword_spaces
        self.additional_params: dict[str, Any] = additional_params or {}

    def get_tesseract_config(self) -> str:
        """Generate Tesseract config string"""
        config_parts = [f"--oem {self.oem_mode.value}", f"--psm {self.psm_mode.value}"]

        if self.preserve_interword_spaces:
            config_parts.append("-c preserve_interword_spaces=1")

        # Add additional parameters
        for key, value in self.additional_params.items():
            config_parts.append(f"-c {key}={value}")

        return " ".join(config_parts)

    def get_language(self) -> str:
        """Get language setting"""
        return self.language


class PreprocessingConfig:
    """Preprocessing Configuration"""

    def __init__(
        self,
        scale_min_height: int = 1000,
        enable_deskew: bool = True,
        enable_background_removal: bool = False,
        denoise_strength: int = 10,
        enable_clahe: bool = True,
        clahe_clip_limit: float = 2.0,
        adaptive_threshold_block_size: int = 15,
        adaptive_threshold_c: int = 5,
        enable_morphology: bool = True,
        morphology_kernel_size: tuple[int, int] = (1, 1),
        morphology_iterations: int = 1,
    ):
        self.scale_min_height: int = scale_min_height
        self.enable_deskew: bool = enable_deskew
        self.enable_background_removal: bool = enable_background_removal
        self.denoise_strength: int = denoise_strength
        self.enable_clahe: bool = enable_clahe
        self.clahe_clip_limit: float = clahe_clip_limit
        self.adaptive_threshold_block_size: int = adaptive_threshold_block_size
        self.adaptive_threshold_c: int = adaptive_threshold_c
        self.enable_morphology: bool = enable_morphology
        self.morphology_kernel_size: tuple[int, int] = morphology_kernel_size
        self.morphology_iterations: int = morphology_iterations


class DocumentProfile:
    """Complete profile combining OCR and preprocessing configs"""

    def __init__(
        self,
        name: str,
        ocr_config: OCRConfig,
        preprocessing_config: PreprocessingConfig,
        description: str = "",
    ):
        self.name: str = name
        self.ocr_config: OCRConfig = ocr_config
        self.preprocessing_config: PreprocessingConfig = preprocessing_config
        self.description: str = description


# Predefined profiles for different document types - ENHANCED
PROFILES = {
    DocumentType.RECEIPT: DocumentProfile(
        name="Receipt",
        description="Optimized for receipts with small text, numbers, and thermal paper",
        ocr_config=OCRConfig(
            psm_mode=PSMMode.SINGLE_BLOCK,
            oem_mode=OEMMode.NEURAL_NET,  # LSTM works better for receipts
            language="eng+spa",
            preserve_interword_spaces=True,
            additional_params={
                "tessedit_char_whitelist": "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzáéíóúüñÁÉÍÓÚÜÑ$€.,:-/() ",
                "textord_heavy_nr": "1",  # Better for noisy images
            },
        ),
        preprocessing_config=PreprocessingConfig(
            scale_min_height=1800,  # Higher resolution for small receipt text
            enable_deskew=True,
            denoise_strength=12,  # Stronger denoising for thermal paper
            enable_clahe=True,
            clahe_clip_limit=3.5,  # Higher contrast for faded receipts
            adaptive_threshold_block_size=9,  # Smaller blocks for fine text
            adaptive_threshold_c=2,
            enable_morphology=True,
            morphology_kernel_size=(1, 1),
            morphology_iterations=1,
        ),
    ),
    DocumentType.INVOICE: DocumentProfile(
        name="Invoice",
        description="Optimized for invoices with tables, structured data, and logos",
        ocr_config=OCRConfig(
            psm_mode=PSMMode.AUTO,
            oem_mode=OEMMode.NEURAL_NET,
            language="eng+spa",
            preserve_interword_spaces=True,
            additional_params={
                "tessedit_pageseg_mode": "1",  # With OSD for better structure detection
            },
        ),
        preprocessing_config=PreprocessingConfig(
            scale_min_height=1400,
            enable_deskew=True,
            denoise_strength=8,
            enable_clahe=True,
            clahe_clip_limit=2.5,
            adaptive_threshold_block_size=13,
            adaptive_threshold_c=4,
            enable_morphology=True,
            morphology_kernel_size=(1, 1),
            morphology_iterations=1,
        ),
    ),
    DocumentType.DOCUMENT: DocumentProfile(
        name="Document",
        description="General documents with paragraphs of text",
        ocr_config=OCRConfig(
            psm_mode=PSMMode.AUTO,
            oem_mode=OEMMode.NEURAL_NET,
            language="eng+spa",
            preserve_interword_spaces=True,
        ),
        preprocessing_config=PreprocessingConfig(
            scale_min_height=1200,
            enable_deskew=True,
            denoise_strength=8,
            enable_clahe=True,
            clahe_clip_limit=2.0,
            adaptive_threshold_block_size=15,
            adaptive_threshold_c=5,
            enable_morphology=False,  # Less aggressive for clean documents
        ),
    ),
    DocumentType.FORM: DocumentProfile(
        name="Form",
        description="Forms with fields, checkboxes, and labels",
        ocr_config=OCRConfig(
            psm_mode=PSMMode.SPARSE_TEXT,  # Better for scattered form fields
            oem_mode=OEMMode.NEURAL_NET,
            language="eng+spa",
            preserve_interword_spaces=True,
            additional_params={
                "tessedit_char_blacklist": "[]{}",  # Avoid confusion with checkboxes
            },
        ),
        preprocessing_config=PreprocessingConfig(
            scale_min_height=1300,
            enable_deskew=True,
            denoise_strength=6,
            enable_clahe=True,
            clahe_clip_limit=2.0,
            adaptive_threshold_block_size=13,
            adaptive_threshold_c=4,
            enable_morphology=True,
            morphology_kernel_size=(1, 1),
            morphology_iterations=1,
        ),
    ),
    DocumentType.SCREENSHOT: DocumentProfile(
        name="Screenshot",
        description="Computer screenshots with clear digital text",
        ocr_config=OCRConfig(
            psm_mode=PSMMode.AUTO,
            oem_mode=OEMMode.NEURAL_NET,  # LSTM works great on digital text
            language="eng+spa",
            preserve_interword_spaces=True,
        ),
        preprocessing_config=PreprocessingConfig(
            scale_min_height=600,  # Screenshots are usually already high-res
            enable_deskew=False,  # Screenshots are usually straight
            denoise_strength=3,  # Minimal denoising for clean digital images
            enable_clahe=False,  # Usually good contrast already
            adaptive_threshold_block_size=11,
            adaptive_threshold_c=2,
            enable_morphology=False,
        ),
    ),
    DocumentType.PHOTO: DocumentProfile(
        name="Photo",
        description="Photos of documents taken with camera/mobile",
        ocr_config=OCRConfig(
            psm_mode=PSMMode.AUTO,
            oem_mode=OEMMode.NEURAL_NET,
            language="eng+spa",
            preserve_interword_spaces=True,
            additional_params={
                "textord_heavy_nr": "1",  # Handle noise from camera
            },
        ),
        preprocessing_config=PreprocessingConfig(
            scale_min_height=1500,
            enable_deskew=True,  # Photos often have skew
            enable_background_removal=True,  # Remove distracting backgrounds
            denoise_strength=15,  # More denoising for camera noise
            enable_clahe=True,
            clahe_clip_limit=3.0,
            adaptive_threshold_block_size=15,
            adaptive_threshold_c=6,
            enable_morphology=True,
            morphology_kernel_size=(2, 2),
            morphology_iterations=1,
        ),
    ),
    DocumentType.HANDWRITTEN: DocumentProfile(
        name="Handwritten",
        description="Handwritten notes and documents",
        ocr_config=OCRConfig(
            psm_mode=PSMMode.SINGLE_BLOCK,
            oem_mode=OEMMode.NEURAL_NET,
            language="eng+spa",
            preserve_interword_spaces=True,
            additional_params={
                "tessedit_pageseg_mode": "6",  # Single uniform block
            },
        ),
        preprocessing_config=PreprocessingConfig(
            scale_min_height=1600,
            enable_deskew=True,
            denoise_strength=10,
            enable_clahe=True,
            clahe_clip_limit=2.5,
            adaptive_threshold_block_size=17,
            adaptive_threshold_c=7,
            enable_morphology=True,
            morphology_kernel_size=(2, 2),
            morphology_iterations=1,
        ),
    ),
    DocumentType.GENERAL: DocumentProfile(
        name="General",
        description="Default profile for unknown document types",
        ocr_config=OCRConfig(
            psm_mode=PSMMode.AUTO,
            oem_mode=OEMMode.NEURAL_NET,
            language="eng+spa",
            preserve_interword_spaces=True,
        ),
        preprocessing_config=PreprocessingConfig(
            scale_min_height=1200,
            enable_deskew=True,
            denoise_strength=10,
            enable_clahe=True,
            clahe_clip_limit=2.0,
            adaptive_threshold_block_size=15,
            adaptive_threshold_c=5,
            enable_morphology=True,
            morphology_kernel_size=(1, 1),
            morphology_iterations=1,
        ),
    ),
}


def get_profile(document_type: DocumentType) -> DocumentProfile:
    """Get a predefined profile by document type"""
    return PROFILES.get(document_type, PROFILES[DocumentType.GENERAL])


def get_profile_by_name(name: str) -> DocumentProfile:
    """Get a profile by name string"""
    try:
        doc_type = DocumentType(name.lower())
        return get_profile(doc_type)
    except ValueError:
        return PROFILES[DocumentType.GENERAL]
