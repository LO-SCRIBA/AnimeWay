import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# DATABASE CON DATI COMPLETI: Includiamo anteprime reali (.png/.jpg) e dettagli grafici
ANIME_DATABASE = [
    {
        "title": "One Piece (Episodi ITA)",
        "id": "one-piece-stream",
        "author": "AnimeUnity",
        "views": "1.2M visualizzazioni",
        "published": "Oggi",
        "duration": "24:00",
        "thumbnail": "https://justwatch.com", # Immagine reale
        "video_url": "http://zencdn.net"
    },
    {
        "title": "Naruto Shippuden (ITA)",
        "id": "naruto-stream",
        "author": "AnimeUnity",
        "views": "900K visualizzazioni",
        "published": "Ieri",
        "duration": "23:20",
        "thumbnail": "https://justwatch.com",
        "video_url": "http://zencdn.net"
    }
]

@app.route('/')
def home():
    return "Proxy Animeway per 3DS attivo e funzionante al 100%!"

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify([])

    results = []
    for anime in ANIME_DATABASE:
        if query in anime["title"].lower() or query == "all" or query == "piece":
            # Inviamo al 3DS esattamente la struttura ricca che si aspetta la UI di FourthTube
            results.append({
                "title": anime["title"],
                "id": anime["id"],
                "author": anime["author"],
                "views": anime["views"],
                "published": anime["published"],
                "duration": anime["duration"],
                "thumbnail": anime["thumbnail"]
            })

    # Se non trova nulla, manda comunque un elemento grafico valido per non far crashare la UI
    if not results:
        results.append({
            "title": f"Avvia {query.capitalize()}",
            "id": f"custom-{query}",
            "author": "Generico",
            "views": "0",
            "published": "Ora",
            "duration": "00:00",
            "thumbnail": ""
        })

    return jsonify(results)

@app.route('/video')
def video():
    video_id = request.args.get('id', '')
    for anime in ANIME_DATABASE:
        if anime["id"] == video_id:
            return jsonify({'url': anime["video_url"]})
    return jsonify({'url': 'http://zencdn.net'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
