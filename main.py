from flask import Flask, render_template, request, jsonify, Response
import os
import google.generativeai as genai

app = Flask(__name__)

# API Key Gemini Anda
GOOGLE_API_KEY = "AQ.Ab8RN6KIkWlPBGLzFJFWlcwdF5NR1LMzcXccBAVsyxj17bFDFQ"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    return render_template('index.html')

# ROUTE OTOMATIS SW.JS: Menghasilkan Service Worker tanpa perlu file sw.js terpisah
@app.route('/sw.js')
def serve_sw():
    sw_code = """
    const CACHE_NAME = 'ai-pwa-cache-v2';
    self.addEventListener('install', e => {
        e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(['/'])));
    });
    self.addEventListener('fetch', e => {
        e.respondWith(caches.match(e.request).then(res => res || fetch(e.request)));
    });
    """
    return Response(sw_code, mimetype='application/javascript')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")
    
    # Deteksi perintah buat foto
    is_image_request = any(word in user_message.lower() for word in ["buat foto", "bikin foto", "gambar", "foto", "generate"])

    if is_image_request:
        try:
            prompt_instruksi = f"Berikan satu kode warna HEX (misal #ff0000) yang paling menggambarkan prompt ini: '{user_message}'. Hanya respons dengan kode warna HEX saja, tidak ada teks lain."
            response = model.generate_content(prompt_instruksi)
            ai_color = response.text.strip()
        except:
            ai_color = "#3357ff"

        return jsonify({
            "type": "image",
            "reply": f"Saya telah memikirkan konsep visual untuk: '{user_message}'",
            "image": {
                "color": ai_color,
                "seed": len(user_message) * 7,
                "prompt_name": user_message
            }
        })
    else:
        try:
            response = model.generate_content(user_message)
            reply = response.text
        except Exception as e:
            reply = f"Aduh, otak Python saya sedang pusing. Error: {str(e)}"
            
        return jsonify({
            "type": "text",
            "reply": reply
        })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
