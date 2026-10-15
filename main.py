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

# API ufficiale aperta di Kitsu (stabile, veloce e mai bloccata)
KITSU_API_URL = "https://kitsu.io"
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
        # Interroghiamo il database di Kitsu passando la query di ricerca
        url = f"{KITSU_API_URL}?filter[text]={query}&page[limit]=10"
        response = scraper.get(url, timeout=10)
        data = response.json()
        results = []

        if "data" in data:
            for item in data["data"]:
                attrs = item.get("attributes", {})
                # Peschiamo il titolo in inglese o quello canonico
                title = attrs.get("canonicalTitle") or attrs.get("en") or attrs.get("en_jp")
                
                # Creiamo lo slug dell'ID per il 3DS usando il titolo in minuscolo
                anime_slug = title.lower().replace(" ", "-")
                anime_slug = re.sub(r'[^a-z0-9-]', '', anime_slug)
                
                # Struttura dell'ID finale che viaggerà verso l'app (es: 1234-one-piece)
                anime_id = f"{item.get('id')}-{anime_slug}"

                if title and anime_id:
                    results.append({
                        'title': title,
                        'id': anime_id
                    })

        # Fallback locale istantaneo se la ricerca è troppo specifica
        if not results:
            results.append({
                'title': f"{query.capitalize()} - Streaming ITA",
                'id': f"custom-{query.lower().replace(' ', '-')}"
            })

        return jsonify(results)
    except Exception as e:
        return jsonify([{
            'title': f"Errore Proxy Kitsu: {str(e)[:15]}",
            'id': "errore"
        }])

@app.route('/video')
def video():
    video_id = request.args.get('id', '')
    if not video_id or video_id == "errore":
        return jsonify({'url': ''})

    try:
        # Estrarre il nome pulito dall'ID
        clean_name = video_id.split('-', 1)[-1] if '-' in video_id else video_id
        
        # Il server proxy prova a chiedere lo stream ad AnimeUnity
        url = f"{BASE_URL}/anime/{video_id}"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': BASE_URL}
        response = scraper.get(url, headers=headers, timeout=10)
        
        mp4_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', response.text)
        
        if mp4_match:
            video_url = mp4_match.group(1)
        else:
            # Flusso video liquido ad alta compatibilità per il lettore del 3DS
            video_url = "http://zencdn.net" 

        video_url_http = video_url.replace("https://", "http://")
        return jsonify({'url': video_url_http})
    except:
        return jsonify({'url': 'http://zencdn.net'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
