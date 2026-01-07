from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
from PyPDF2 import PdfReader
import io
import os

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# 🔑 Set API key safely (env variable)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyBzzrqsAFRr8yssq571eO0U1vzIaDCP7cg"))

model = genai.GenerativeModel("gemini-2.5-flash")

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/analyze", methods=["POST"])
def analyze_resume():
    try:
        job_title = request.form.get("jobTitle", "Professional Role")
        file = request.files.get("resume")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        pdf_bytes = io.BytesIO(file.read())
        resume_text = extract_text_from_pdf(pdf_bytes)

        if len(resume_text.strip()) < 100:
            return jsonify({"error": "PDF text too short or scanned"}), 400

        system_prompt = f"""
        Analyze the resume for the job: "{job_title}"

        Respond strictly in JSON:
        {{
            "score": number,
            "label": "Brief status",
            "feedback": [{{"title": "str", "desc": "str"}}],
            "strengths": ["str"],
            "keywords": ["str"]
        }}
        """

        response = model.generate_content(
            [system_prompt, resume_text],
            generation_config={"response_mime_type": "application/json"}
        )

        return jsonify(response.candidates[0].content.parts[0].text)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
