import os
import re
from flask import Flask, jsonify, request
import cloudscraper

app = Flask(__name__)

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

KITSU_API_URL = "https://kitsu.io/api/edge/anime"
BASE_URL = "https://animeunity.so"

@app.route('/')
def home():
    return "Proxy Animeway per 3DS attivo e funzionante al 100%!"

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    try:
        url = f"{KITSU_API_URL}?filter[text]={query}&page[limit]=10"
        
        # UTILI ED OBBLIGATORI: Diciamo a Kitsu che siamo un'applicazione conforme alle sue regole JSON:API
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/vnd.api+json'
        }
        
        response = scraper.get(url, headers=headers, timeout=10)
        data = response.json()
        results = []

        if "data" in data:
            for item in data["data"]:
                attrs = item.get("attributes", {})
                title = attrs.get("canonicalTitle") or attrs.get("en") or attrs.get("en_jp")
                
                # Creiamo l'ID compatibile per la ricerca del 3DS
                anime_slug = title.lower().replace(" ", "-")
                anime_slug = re.sub(r'[^a-z0-9-]', '', anime_slug)
                anime_id = f"{item.get('id')}-{anime_slug}"

                if title and anime_id:
                    results.append({
                        'title': title,
                        'id': anime_id
                    })

        # Se il database non restituisce nulla, creiamo al volo un elemento con la parola cercata
        if not results:
            results.append({
                'title': f"{query.capitalize()} - Avvia Streaming",
                'id': f"custom-{query.lower().replace(' ', '-')}"
            })

        return jsonify(results)
    except Exception as e:
        # Mostriamo l'errore direttamente nella lista se qualcosa va storto
        return jsonify([{
            'title': f"Errore Proxy: {str(e)[:20]}",
            'id': "errore"
        }])

@app.route('/video')
def video():
    video_id = request.args.get('id', '')
    if not video_id or video_id == "errore":
        return jsonify({'url': ''})

    try:
        url = f"{BASE_URL}/anime/{video_id}"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': BASE_URL}
        response = scraper.get(url, headers=headers, timeout=10)
        
        mp4_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', response.text)
        
        if mp4_match:
            video_url = mp4_match.group(1)
        else:
            video_url = "http://zencdn.net" 

        video_url_http = video_url.replace("https://", "http://")
        return jsonify({'url': video_url_http})
    except:
        return jsonify({'url': 'http://zencdn.net'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
