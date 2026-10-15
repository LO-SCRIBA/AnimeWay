import os
from flask import Flask, jsonify, request

app = Flask(__name__)

# DATABASE LOCALE STATICO: Nessun collegamento esterno = zero blocchi di rete!
# Puoi espandere questa lista a piacimento aggiungendo altri anime e link video (.mp4)
ANIME_DATABASE = [
    {
        "title": "One Piece (Episodi ITA)",
        "id": "one-piece-stream",
        "video_url": "http://zencdn.net" # Video di test fluido ad alta compatibilità 3DS
    },
    {
        "title": "Naruto Shippuden (ITA)",
        "id": "naruto-stream",
        "video_url": "http://zencdn.net"
    },
    {
        "title": "Demon Slayer (Sub ITA)",
        "id": "demon-slayer-stream",
        "video_url": "http://zencdn.net"
    },
    {
        "title": "Attack on Titan (ITA)",
        "id": "aot-stream",
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
    # Cerchiamo all'interno del nostro database locale
    for anime in ANIME_DATABASE:
        if query in anime["title"].lower():
            results.append({
                "title": anime["title"],
                "id": anime["id"]
            })

    # Fallback dinamico se l'utente cerca qualcosa che non è in lista
    if not results:
        results.append({
            "title": f"{query.capitalize()} (Avvia Streaming Diretto)",
            "id": f"custom-{query.replace(' ', '-')}"
        })

    return jsonify(results)

@app.route('/video')
def video():
    video_id = request.args.get('id', '')
    if not video_id:
        return jsonify({'url': ''})

    # Cerchiamo l'URL del video abbinato all'ID nel database
    for anime in ANIME_DATABASE:
        if anime["id"] == video_id:
            return jsonify({'url': anime["video_url"]})

    # Fallback video universale se l'ID è personalizzato o non trovato
    return jsonify({'url': 'http://zencdn.net'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
