import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")


def analyze_resume(resume_text):

    prompt = f"""
    Analyze this resume and provide:

    1. Resume Score out of 100
    2. Top Strengths
    3. Weaknesses
    4. Improvement Tips

    Resume:
    {resume_text}
    """

    response = model.generate_content(prompt)

    return response.text