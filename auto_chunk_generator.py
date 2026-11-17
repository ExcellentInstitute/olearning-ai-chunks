import os
import json
import time
import PyPDF2
import google.generativeai as genai

# --- 1. SETTINGS ---
# Put your free Gemini API Key here (same one you use in Android Studio)
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# Put the exact name of the PDF file you placed in this folder
BOOK_FILE_NAME = "my_science_book.pdf"

# Put the exact Subject Name as it appears in your Android App (e.g., "ଗଣିତ" or "Study Material")
SUBJECT_NAME_IN_APP = "Study Material"


# --- 2. LOGIC ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_java_hash_code(s):
    """Calculates the exact same Hash ID that Android Kotlin uses, so the app finds the right file."""
    h = 0
    for c in s:
        h = (31 * h + ord(c)) & 0xFFFFFFFF
    return ((h + 0x80000000) & 0xFFFFFFFF) - 0x80000000

def generate_page_answers(page_text):
    prompt = f"""
    You are Foxy, a helpful teacher for school children. Read this page from a textbook.
    Generate a JSON response strictly in this format, written in simple Odia script:
    {{
        "qna": "୧. ପ୍ରଶ୍ନ: ... \\nଉତ୍ତର: ... (Generate 3 to 5 important exam Q&A from this page)",
        "story": "ପିଲାମାନେ, ଆଜି ଆମେ... (Explain the core concept of this page like an easy, fun story)",
        "words": "୧. ଶବ୍ଦ = ଅର୍ଥ (List 3 to 5 difficult words found on this page and their Odia meanings)",
        "keywords": {{
            "ଖାଦ୍ୟ": "ଖାଦ୍ୟ ହେଉଛି...",
            "EnglishWord": "Odia meaning..."
        }}
    }}
    Do NOT use markdown outside the JSON. Ensure it is valid JSON.
    Here is the page text:
    {page_text}
    """
    try:
        response = model.generate_content(prompt)
        json_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return None

def process_book():
    subject_id = abs(get_java_hash_code(SUBJECT_NAME_IN_APP))
    print(f"📚 Starting book: {SUBJECT_NAME_IN_APP} (App ID: {subject_id})")

    if not os.path.exists("chunks"):
        os.makedirs("chunks")

    with open(BOOK_FILE_NAME, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        total_pages = len(reader.pages)

        for i in range(total_pages):
            page_num = i + 1  # Android app pages start at 1
            print(f"⏳ Reading Page {page_num} of {total_pages}...")

            text = reader.pages[i].extract_text()
            if not text or len(text.strip()) < 30:
                print(f"⚠️ Page {page_num} is empty or just images. Skipping.")
                continue

            chunk_data = generate_page_answers(text)

            if chunk_data:
                file_name = f"chunks/sub_{subject_id}_p{page_num}.json"
                with open(file_name, 'w', encoding='utf-8') as outfile:
                    json.dump(chunk_data, outfile, ensure_ascii=False, indent=4)
                print(f"✅ Success! Saved {file_name}")

            # Pause for 4 seconds so Google doesn't block the free tier limit (15 requests/minute)
            time.sleep(4)

if __name__ == "__main__":
    if os.path.exists(BOOK_FILE_NAME):
        process_book()
        print("\n🎉 ALL DONE! Upload the 'chunks' folder to your free GitHub Repository.")
    else:
        print(f"❌ Error: Please put '{BOOK_FILE_NAME}' in this folder first!")
