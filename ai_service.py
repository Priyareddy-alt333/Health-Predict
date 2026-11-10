

import os
import time
from google import genai


def generate_health_remarks(glucose, haemoglobin, cholesterol):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "AI service unavailable: Gemini API key is not configured."

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are assisting with an educational blood test record application.

    Review these reported values:
    Glucose: {glucose}
    Haemoglobin: {haemoglobin}
    Cholesterol: {cholesterol}

    Write a short, cautious explanation of what these values
    may warrant reviewing.

    Important:
    - Do not diagnose any disease.
    - Do not claim certainty or predict a confirmed condition.
    - The units and fasting status have not been provided.
    - Haemoglobin interpretation depends on age, sex and
      laboratory reference ranges.
    - Explain that a healthcare professional should interpret
      the results using the original laboratory report.
    - Do not invent missing patient information.
    """

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if not response.text:
                return "AI service returned no remarks."

            return response.text.strip()

        except Exception as exc:
            error_message = str(exc)

            print(
                f"Gemini API attempt {attempt + 1} failed:",
                type(exc).__name__,
                error_message
            )

            if "503" in error_message and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue

            if "503" in error_message:
                return (
                    "AI remarks pending: Gemini is temporarily busy. "
                    "Please try again later."
                )

            return (
                "AI service unavailable. "
                "Please check the API configuration."
            )

    return "AI remarks pending. Please try again later."