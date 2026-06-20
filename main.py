from flask import Flask, request, jsonify, Response
import os
import google.generativeai as genai

app = Flask(__name__)

# API Key Gemini Anda
GOOGLE_API_KEY = "AQ.Ab8RN6KIkWlPBGLzFJFWlcwdF5NR1LMzcXccBAVsyxj17bFDFQ"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# KODE HTML LANGSUNG DI DALAM PYTHON (Agar Ringkas & Anti-Error di Vercel)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Python Chat & Image Generator</title>
    <link rel="manifest" href="data:application/manifest+json,%7B%22name%22%3A%22Python%20AI%20Studio%20App%22%2C%22short_name%22%3A%22PythonAI%22%2C%22start_url%22%3A%22%2F%22%2C%22display%22%3A%22standalone%22%2C%22background_color%22%3A%22%231a1a2e%22%2C%22theme_color%22%3A%22%23162447%22%2C%22orientation%22%3A%22portrait%22%2C%22icons%22%3A%5B%7B%22src%22%3A%22https%3A%2F%2Fcdn-icons-png.flaticon.com%2F512%2F1693%2F1693746.png%22%2C%22sizes%22%3A%22512x512%22%2C%22type%22%3A%22image%22%7D%5D%7D">
    <meta name="theme-color" content="#162447">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #1a1a2e; color: #ffffff; display: flex; flex-direction: column; height: 100vh; }
        header { background-color: #162447; padding: 15px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.3); }
        #chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .message { max-width: 80%; padding: 12px 16px; border-radius: 15px; line-height: 1.4; word-wrap: break-word; }
        .user { align-self: flex-end; background-color: #e43f5a; border-bottom-right-radius: 2px; }
        .ai { align-self: flex-start; background-color: #1f4068; border-bottom-left-radius: 2px; white-space: pre-wrap; }
        .input-area { background-color: #162447; padding: 15px; display: flex; gap: 10px; }
        input { flex: 1; padding: 12px; border: none; border-radius: 25px; background-color: #1a1a2e; color: white; outline: none; }
        button { background-color: #e43f5a; color: white; border: none; padding: 0 20px; border-radius: 25px; cursor: pointer; font-weight: bold; }
        canvas { display: block; margin-top: 10px; max-width: 100%; border-radius: 8px; border: 2px solid #e43f5a; }
    </style>
</head>
<body>
    <header><h2>Python AI Studio PWA</h2></header>
    <div id="chat-container">
        <div class="message ai">Halo! Saya bertenaga Gemini 1.5 Flash. Tanya apa saja atau ketik "Buat foto [tema]" untuk menyuruh saya merancang objek visual.</div>
    </div>
    <div class="input-area">
        <input type="text" id="user-input" placeholder="Tanya sesuatu atau minta buat foto...">
        <button onclick="sendMessage()">Kirim</button>
    </div>
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').catch(err => console.log('PWA Gagal:', err));
            });
        }
        async function sendMessage() {
            const inputEl = document.getElementById('user-input');
            const message = inputEl.value.trim();
            if (!message) return;
            appendMessage(message, 'user');
            inputEl.value = '';
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                const data = await response.json();
                appendMessage(data.reply, 'ai');
                if (data.type === 'image') { renderAIImage(data.image); }
            } catch (error) { appendMessage('Waduh, koneksi terputus!', 'ai'); }
        }
        function appendMessage(text, sender) {
            const container = document.getElementById('chat-container');
            const msgDiv = document.createElement('div');
            msgDiv.classList.add('message', sender);
            msgDiv.innerText = text;
            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        }
        function renderAIImage(imgData) {
            const container = document.getElementById('chat-container');
            const canvas = document.createElement('canvas');
            canvas.width = 300; canvas.height = 300;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = imgData.color; ctx.fillRect(0, 0, 300, 300);
            ctx.fillStyle = "rgba(255, 255, 255, 0.2)";
            for (let i = 0; i < 6; i++) {
                ctx.beginPath(); ctx.arc(150 + (i * 8), 150 - (i * 4), 40 + (imgData.seed % 60), 0, Math.PI * 2); ctx.fill();
            }
            ctx.fillStyle = "#ffffff"; ctx.font = "14px Arial";
            ctx.fillText("Visual: " + imgData.prompt_name, 10, 280);
            container.appendChild(canvas);
            container.scrollTop = container.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/sw.js')
def serve_sw():
    sw_code = """
    const CACHE_NAME = 'ai-pwa-cache-v2';
    self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(['/']))); });
    self.addEventListener('fetch', e => { e.respondWith(caches.match(e.request).then(res => res || fetch(e.request))); });
    """
    return Response(sw_code, mimetype='application/javascript')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")
    is_image_request = any(word in user_message.lower() for word in ["buat foto", "bikin foto", "gambar", "foto", "generate"])

    if is_image_request:
        try:
            prompt_instruksi = f"Berikan satu kode warna HEX (misal #ff0000) yang paling menggambarkan prompt ini: '{user_message}'. Hanya respons dengan kode warna HEX saja, tidak ada teks lain."
            response = model.generate_content(prompt_instruksi)
            ai_color = response.text.strip()
        except:
            ai_color = "#3357ff"
        return jsonify({"type": "image", "reply": f"Visual terkonsep: '{user_message}'", "image": {"color": ai_color, "seed": len(user_message) * 7, "prompt_name": user_message}})
    else:
        try:
            response = model.generate_content(user_message)
            reply = response.text
        except Exception as e:
            reply = f"Error mendengarkan otak Python: {str(e)}"
        return jsonify({"type": "text", "reply": reply})

# PENTING UNTUK VERCEL: Agar aplikasi diekspor dengan benar
# Anda bisa menghapus block if __name__ == '__main__' lama
