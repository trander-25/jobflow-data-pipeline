from api.config import Settings


class GenAIClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None

    def generate(self, prompt: str) -> str:
        if not self.settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is not configured")

        if self.client is None:
            from google import genai
            from google.genai import types

            self.client = genai.Client(api_key=self.settings.google_api_key)
        else:
            from google.genai import types

        response = self.client.models.generate_content(
            model=self.settings.google_genai_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=self.settings.google_genai_temperature),
        )
        text = getattr(response, "text", None)
        if text:
            return text.strip()
        return "JobFlow chưa nhận được nội dung trả lời từ model AI."
