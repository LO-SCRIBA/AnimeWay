import os
import re
from flask import Flask, jsonify, request
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configurazione del browser per superare i controlli del sito
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

BASE_URL = "https://animeunity.to"

@app.route('/')
def home():
    return "Proxy AnimeUnity per 3DS attivo e funzionante!"

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    try:
        # Effettuiamo la ricerca su AnimeUnity
        url = f"{BASE_URL}/anime?search={query}"
        response = scraper.get(url, timeout=10)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # AnimeUnity mostra le schede degli anime tramite tag 'a' specifici
        # Cerchiamo tutti i blocchi che contengono i link degli anime
        for card in soup.select('a[href*="/anime/"]'):
            href = card.get('href', '')
            
            # Estraiamo l'ID/Slug (es. /anime/123-one-piece -> 123-one-piece)
            anime_id = href.replace(BASE_URL, "").replace("/anime/", "").strip("/")
            
            # Cerchiamo il titolo all'interno dei tag interni (h2, h3, o la classe title)
            title_el = card.select_one('.title, h2, h3, .name')
            title = title_el.text.strip() if title_el else card.get('title', '').strip()
            
            # Se il titolo non c'è, proviamo a ricavarlo pulendo l'ID
            if not title and anime_id:
                title = anime_id.split('-', 1)[-1].replace('-', ' ').title()

            if title and anime_id:
                # Evitiamo duplicati nella lista
                if not any(r['id'] == anime_id for r in results):
                    results.append({
                        'title': title,
                        'id': anime_id
                    })

        # Se il sito ha cambiato layout e non trova nulla, mandiamo un dato di test per sbloccare la UI del 3DS
        if not results:
            results.append({
                'title': f"Nessun risultato trovato per '{query}'",
                'id': "non-trovato"
            })

        return jsonify(results)
    except Exception as e:
        # In caso di errore di connessione, mandiamo comunque un JSON valido che il 3DS può mostrare
        return jsonify([{
            'title': f"Errore Server Proxy: {str(e)[:25]}",
            'id': "errore-rete"
        }])

@app.route('/video')
def video():
    video_id = request.args.get('id', '')
    if not video_id or video_id in ["non-trovato", "errore-rete"]:
        return jsonify({'url': ''})

    try:
        # Carichiamo la pagina dell'anime/episodio
        url = f"{BASE_URL}/anime/{video_id}"
        response = scraper.get(url, timeout=10)
        
        # Cerchiamo il link al file .mp4 diretto nel codice sorgente
        mp4_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', response.text)
        
        if mp4_match:
            video_url = mp4_match.group(1)
        else:
            # Se non c'è il link diretto, cerchiamo il player embedded (iframe)
            soup = BeautifulSoup(response.text, 'html.parser')
            iframe = soup.select_one('iframe[src*="embed"], iframe[src*="player"]')
            if iframe:
                iframe_url = iframe.get('src', '')
                iframe_res = scraper.get(iframe_url, timeout=10)
                embed_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', iframe_res.text)
                video_url = embed_match.group(1) if embed_match else ""
            else:
                video_url = ""

        # Rimuoviamo l'HTTPS per aggirare i vecchi certificati del 3DS
        video_url_http = video_url.replace("https://", "http://")
        return jsonify({'url': video_url_http})
    except:
        return jsonify({'url': ''})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
