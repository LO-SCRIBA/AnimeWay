import os
import re
from flask import Flask, jsonify, request
import cloudscraper
from bs4 import BeautifulSoup

app = Flask(__name__)

# Usiamo cloudscraper per bypassare le protezioni Cloudflare di AnimeUnity
scraper = cloudscraper.create_scraper()
BASE_URL = "https://animeunity.to" # Dominio di riferimento per AnimeUnity

@app.route('/')
def home():
    return "Proxy AnimeUnity per 3DS attivo e funzionante!"

# 1. ENDPOINT DI RICERCA ANIME
@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    try:
        # Effettua la ricerca sul sito
        response = scraper.get(f"{BASE_URL}/anime?search={query}")
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Trova i blocchi degli anime nella pagina di ricerca
        # Nota: I selettori di classe '.anime-card' o '.archive-post' variano se il sito si aggiorna
        for card in soup.select('.anime-card, .archive-post, a[href*="/anime/"]'):
            title_element = card.select_one('.title, h3, h2')
            title = title_element.text.strip() if title_element else card.get('title', 'Anime Senza Titolo')
            
            link = card.get('href', '')
            # Estraiamo l'ID o lo slug dell'anime dall'URL (es: /anime/1234-titolo)
            anime_id = link.replace(BASE_URL, "").replace("/anime/", "")

            if title and anime_id:
                results.append({
                    'title': title,
                    'id': anime_id
                })

        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. ENDPOINT PER LISTA EPISODI
@app.route('/episodes')
def episodes():
    anime_id = request.args.get('id', '')
    if not anime_id:
        return jsonify([])

    try:
        # Carica la pagina principale dell'anime per vedere gli episodi
        response = scraper.get(f"{BASE_URL}/anime/{anime_id}")
        soup = BeautifulSoup(response.text, 'html.parser')
        episodes_list = []

        # Cerca i link o i bottoni degli episodi
        for ep_box in soup.select('.episodes-wrapper a, .episode-item, a[href*="-ep-"]'):
            ep_url = ep_box.get('href', '')
            ep_num = ep_box.text.strip()
            
            ep_id = ep_url.replace(BASE_URL, "").replace("/anime/", "")
            
            episodes_list.append({
                'number': ep_num,
                'id': ep_id
            })

        return jsonify(episodes_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 3. ENDPOINT PER OTTENERE IL LINK VIDEO DIRETTO (.MP4)
@app.route('/video')
def video():
    ep_id = request.args.get('id', '')
    if not ep_id:
        return jsonify({'error': 'Missing episode id'}), 400

    try:
        # Carica la pagina dell'episodio specifico
        response = scraper.get(f"{BASE_URL}/anime/{ep_id}")
        
        # Gli streaming di AnimeUnity spesso nascondono il file MP4 dentro script or player iframe (es. Vivamonos, Wstream, o player interno)
        # Cerchiamo pattern video comuni o indirizzi mp4 diretti nel codice sorgente della pagina
        video_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', response.text)
        
        if video_match:
            video_url = video_match.group(1)
        else:
            # Se è dentro un iframe (es. player esterno), proviamo a estrarre la sorgente del player
            soup = BeautifulSoup(response.text, 'html.parser')
            iframe = soup.select_one('iframe[src*="embed"], iframe[src*="player"]')
            if iframe:
                iframe_url = iframe.get('src', '')
                # Entriamo nell'iframe per cercare il file MP4
                iframe_res = scraper.get(iframe_url)
                mp4_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', iframe_res.text)
                video_url = mp4_match.group(1) if mp4_match else "Video non trovato nel player"
            else:
                return jsonify({'error': 'Video stream non trovato. Potrebbe richiedere decodifica avanzata'}), 404

        # Il 3DS non digerisce i link HTTPS moderni nei player di FourthTube.
        # Trucco: Forziamo la stringa in HTTP semplice se il server di destinazione lo accetta,
        # oppure lasciamo che FourthTube la gestisca tramite i tuoi test di rete.
        video_url_http = video_url.replace("https://", "http://")

        return jsonify({'url': video_url_http})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Render assegna una porta dinamica tramite variabile d'ambiente, altrimenti usa la 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
