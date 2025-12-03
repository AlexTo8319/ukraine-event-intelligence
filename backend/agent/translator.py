"""Translation functionality for event titles and descriptions."""
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class Translator:
    """Translates Ukrainian text to English using OpenAI."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def is_ukrainian(self, text: str) -> bool:
        """Check if text contains Ukrainian characters."""
        if not text:
            return False
        # Ukrainian Cyrillic range
        ukrainian_chars = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
        return any(char.lower() in ukrainian_chars for char in text)
    
    def translate(self, text: str, context: str = "event title") -> str:
        """
        Translate Ukrainian text to English.
        
        Args:
            text: Text to translate
            context: Context for translation (e.g., "event title", "event description")
            
        Returns:
            Translated text, or original if not Ukrainian or translation fails
        """
        if not text or not self.is_ukrainian(text):
            return text
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. Translate Ukrainian text to English. Preserve the meaning and tone. For {context}, keep it concise and professional."
                    },
                    {
                        "role": "user",
                        "content": f"Translate this Ukrainian text to English: {text}"
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            translated = response.choices[0].message.content.strip()
            return translated
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original on error



