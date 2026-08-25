import os
from typing import Optional
from app.core.config import settings
from app.engine.providers.base_provider import BaseLLMProvider, LLMRecommendationSchema

class OpenAILLMProvider(BaseLLMProvider):
    """Production OpenAI LLM Provider utilizing OpenAI Structured Outputs API."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.LLM_API_KEY or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name or settings.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Set LLM_API_KEY environment variable.")

        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("The 'openai' package is required for OpenAILLMProvider. Install with `pip install openai`.")

    def generate_recommendation(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> LLMRecommendationSchema:
        system_content = system_instruction or (
            "You are RecoverAI's AI Payment Recovery Engine specializing in Indian payment gateway failure recovery (Razorpay ecosystem). "
            "Analyze payment failure telemetry and return a structured recovery recommendation."
        )

        response = self.client.beta.chat.completions.parse(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            response_format=LLMRecommendationSchema,
            temperature=settings.LLM_TEMPERATURE
        )

        recommendation = response.choices[0].message.parsed
        if not recommendation:
            raise ValueError("OpenAI returned null parsed output for structured recommendation.")

        return recommendation
