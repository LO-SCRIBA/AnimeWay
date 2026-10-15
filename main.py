import os
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "Catalogo Anime Libero per 3DS attivo!"

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    try:
        # Interroghiamo l'API ufficiale e aperta di Internet Archive.
        # Cerchiamo file video (.mp4) in italiano basandoci sulla parola scritta sul 3DS.
        search_url = f"https://archive.org{query}+AND+mediatype:movies+AND+format:MP4&fl[]=identifier,title&output=json"
        
        response = requests.get(search_url, timeout=10)
        data = response.json()
        results = []

        if "response" in data and "docs" in data["response"]:
            for doc in data["response"]["docs"]:
                title = doc.get("title", "Anime senza titolo")
                # L'identifier è l'ID univoco dell'archivio video su Archive.org
                identifier = doc.get("identifier")

                if title and identifier:
                    results.append({
                        "title": title,
                        "id": identifier,
                        "author": "Internet Archive",
                        "views": "Disponibile",
                        "published": "Open Source",
                        "duration": "24:00",
                        "thumbnail": ""
                    })

        # Se non trova nulla, restituiamo un elemento di cortesia
        if not results:
            results.append({
                "title": f"Nessun archivio trovato per '{query}'",
                "id": "vuoto",
                "author": "-", "views": "-", "published": "-", "duration": "-", "thumbnail": ""
            })

        return jsonify(results)
    except Exception as e:
        return jsonify([{"title": f"Errore: {str(e)[:20]}", "id": "error", "author": "-", "views": "-", "published": "-", "duration": "-", "thumbnail": ""}])

@app.route('/video')
def video():
    identifier = request.args.get('id', '')
    if not identifier or identifier in ["vuoto", "error"]:
        return jsonify({'url': ''})

    try:
        # Su Archive.org, una volta ottenuto l'identifier, l'URL del file video .mp4 
        # è standard, fisso e pubblico. Non serve fare scraping delle pagine!
        # Chiediamo i dettagli dei file per trovare il nome esatto dell'MP4
        meta_url = f"https://archive.org{identifier}"
        meta_res = requests.get(meta_url, timeout=10).json()
        
        mp4_filename = ""
        if "files" in meta_res:
            for file_info in meta_res["files"]:
                if file_info.get("format") == "MP4":
                    mp4_filename = file_info.get("name")
                    break
        
        if mp4_filename:
            # Componiamo il link del file video diretto in chiaro
            video_url = f"http://archive.org{identifier}/{mp4_filename}"
            return jsonify({'url': video_url})
            
    except:
        pass
        
    return jsonify({'url': ''})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
