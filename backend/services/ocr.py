"""OCR service using Tesseract for local text extraction from images."""
from __future__ import annotations

import logging
from pathlib import Path

import pytesseract
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger("fragdieki.ocr")


class OCRServiceUnavailableError(RuntimeError):
    """Raised when OCR cannot run because Tesseract is unavailable."""


class OCRService:
    """Local OCR service using Tesseract."""

    def __init__(self, language: str = "deu"):
        """
        Initialize OCR service.

        Args:
            language: Tesseract language code (e.g., 'deu' for German, 'eng' for English)
        """
        self.language = language
        self._available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available."""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR available: version %s", version)
            return True
        except Exception as e:
            logger.warning("Tesseract not found or not responding: %s", e)
            return False

    def ready(self) -> str:
        """Check if OCR service is ready."""
        return "ready" if self._available else "unavailable"

    def extract_text(self, image_path: Path) -> str:
        """
        Extract text from an image using Tesseract OCR.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text as a string

        Raises:
            ValueError: If no text is found or image is invalid
            RuntimeError: If OCR processing fails
        """
        if not image_path.exists():
            raise ValueError(f"Image file not found: {image_path}")
        if not self._available:
            raise OCRServiceUnavailableError("OCR service unavailable")

        try:
            # Open and validate image
            with Image.open(image_path) as img:
                # Auto-rotate based on EXIF orientation
                img = self._apply_exif_orientation(img)

                # Convert to RGB if needed (Tesseract works best with RGB)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Run Tesseract OCR with German language
                # PSM 3 = Fully automatic page segmentation, but no OSD (Orientation and Script Detection)
                config = f"--psm 3 -l {self.language}"
                text = pytesseract.image_to_string(img, config=config)

                # Clean up the extracted text: strip and normalize whitespace
                # split() without args splits on any whitespace and removes empty strings
                text = " ".join(text.split())

                if not text:
                    raise ValueError("No text found in image")

                logger.info("OCR extracted %d characters from %s", len(text), image_path.name)
                return text

        except UnidentifiedImageError as e:
            logger.error("Invalid image file %s: %s", image_path, e)
            raise ValueError(f"Invalid image file: {e}") from e
        except pytesseract.TesseractError as e:
            logger.error("Tesseract failed for %s: %s", image_path, e)
            raise RuntimeError(f"OCR processing failed: {e}") from e
        except Exception as e:
            logger.error("OCR failed for %s: %s", image_path, e)
            raise

    def _apply_exif_orientation(self, img: Image.Image) -> Image.Image:
        """
        Apply EXIF orientation to image if present.

        Args:
            img: PIL Image object

        Returns:
            Rotated image if EXIF orientation is present, otherwise original image
        """
        try:
            exif = img.getexif()
            if exif is not None:
                orientation = exif.get(0x0112)  # Orientation tag
                if orientation:
                    # Apply rotation based on EXIF orientation
                    rotation_map = {
                        3: 180,
                        6: 270,
                        8: 90,
                    }
                    if orientation in rotation_map:
                        img = img.rotate(rotation_map[orientation], expand=True)
                        logger.debug("Applied EXIF rotation: %d degrees", rotation_map[orientation])
        except Exception as e:
            logger.warning("Could not apply EXIF orientation: %s", e)

        return img
