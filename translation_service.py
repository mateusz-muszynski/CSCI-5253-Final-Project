"""
Google Cloud Translation API integration for language detection and translation.
"""
import logging
from typing import Tuple, Optional
from google.cloud import translate_v2 as translate

from config import Config

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for language detection and translation using Google Cloud Translation API."""
    
    def __init__(self):
        """Initialize Translation API client."""
        try:
            self.client = translate.Client()
            logger.info("Translation service initialized")
        except Exception as e:
            logger.error(f"Error initializing translation service: {str(e)}")
            raise
    
    def detect_and_translate(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect the language of the text and translate it to English.
        
        Args:
            text: Text to detect and translate
            
        Returns:
            Tuple of (detected_language_code, translated_text)
        """
        try:
            if not Config.TRANSLATION_API_ENABLED:
                logger.warning("Translation API is disabled in config")
                return None, None
            
            # Detect language
            detection_result = self.client.detect_language(text)
            detected_language = detection_result.get("language", "unknown")
            confidence = detection_result.get("confidence", 0.0)
            
            logger.info(f"Detected language: {detected_language} (confidence: {confidence})")
            
            # If already English, return as is
            if detected_language == "en":
                logger.info("Text is already in English, skipping translation")
                return "en", text
            
            # Translate to English
            translation_result = self.client.translate(
                text,
                target_language="en"
            )
            
            translated_text = translation_result.get("translatedText", text)
            logger.info(f"Translated text from {detected_language} to English")
            
            return detected_language, translated_text
            
        except Exception as e:
            logger.error(f"Error in translation service: {str(e)}")
            # Return None values on error - the system can still process without translation
            return None, None

