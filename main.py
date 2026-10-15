import os
import re
from flask import Flask, jsonify, request
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

# Configurazione del browser per superare i blocchi anti-bot
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

# AGGIORNATO: Usiamo il dominio ufficiale funzionante
BASE_URL = "https://www.animeunity.so"

@app.route('/')
def home():
    return "Proxy AnimeUnity per 3DS attivo e funzionante!"

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    try:
        # Inviamo la query di ricerca al sito ufficiale
        url = f"{BASE_URL}/anime?search={query}"
        response = scraper.get(url, timeout=10)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Cerchiamo i link degli anime. AnimeUnity usa la struttura standard /anime/ID-titolo
        for card in soup.find_all('a', href=True):
            href = card['href']
            if '/anime/' in href:
                # Estraiamo l'ID/Slug pulito rimuovendo l'URL di base
                anime_id = href.replace(BASE_URL, "").replace("/anime/", "").strip("/")
                
                # Evitiamo di prendere frammenti di link o pagine di episodi singoli
                if not anime_id or "/" in anime_id:
                    continue
                    
                # Estraiamo il titolo testuale
                title_el = card.select_one('.title, h2, h3, .name')
                title = title_el.text.strip() if title_el else card.get('title', '').strip()
                
                if not title:
                    title = card.text.strip()

                if title and anime_id:
                    # Evitiamo duplicati nella lista
                    if not any(r['id'] == anime_id for r in results):
                        results.append({
                            'title': title,
                            'id': anime_id
                        })

        # Se non trova risultati reali, mandiamo un dato simulato per sbloccare l'app
        if not results:
            # Proviamo un fallback con ricerca testuale generica se il DOM è cambiato
            results.append({
                'title': f"Nessun risultato trovato per '{query}'",
                'id': "non-trovato"
            })

        return jsonify(results)
    except Exception as e:
        return jsonify([{
            'title': f"Errore di Connessione: {str(e)[:25]}",
            'id': "errore-rete"
        }])

@app.route('/video')
def video():
    video_id = request.args.get('id', '')
    if not video_id or video_id in ["non-trovato", "errore-rete"]:
        return jsonify({'url': ''})

    try:
        url = f"{BASE_URL}/anime/{video_id}"
        response = scraper.get(url, timeout=10)
        
        # Cerchiamo il file video diretto .mp4
        mp4_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', response.text)
        
        if mp4_match:
            video_url = mp4_match.group(1)
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            iframe = soup.select_one('iframe[src*="embed"], iframe[src*="player"]')
            if iframe:
                iframe_url = iframe.get('src', '')
                iframe_res = scraper.get(iframe_url, timeout=10)
                embed_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', iframe_res.text)
                video_url = embed_match.group(1) if embed_match else ""
            else:
                video_url = ""

        video_url_http = video_url.replace("https://", "http://")
        return jsonify({'url': video_url_http})
    except:
        return jsonify({'url': ''})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
