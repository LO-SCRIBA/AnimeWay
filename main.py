import os
import re
from flask import Flask, jsonify, request
import cloudscraper

app = Flask(__name__)

# Configurazione ottimizzata di cloudscraper per simulare un vero PC ed evitare i blocchi anti-bot
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

# Il dominio ufficiale attivo verificato
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
        # Molti siti moderni caricano i risultati tramite un'API interna di ricerca.
        # Interroghiamo direttamente la barra degli indirizzi simulando i parametri completi.
        url = f"{BASE_URL}/anime"
        params = {'search': query}
        
        # Effettuiamo la chiamata inviando le intestazioni standard di Chrome
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': BASE_URL
        }
        
        response = scraper.get(url, params=params, headers=headers, timeout=10)
        results = []

        # Usiamo un'espressione regolare robusta direttamente sul testo grezzo per estrarre 
        # i link degli anime (/anime/ID-slug) e i titoli, superando i cambiamenti del layout HTML.
        matches = re.findall(r'href=["\']/anime/([^"\']+)["\'][^>]*>(.*?)</a>', response.text, re.DOTALL)
        
        for anime_id, title_raw in matches:
            anime_id = anime_id.strip("/")
            
            # Escludiamo link a pagine di navigazione generiche o doppie
            if not anime_id or "/" in anime_id or "pages" in anime_id:
                continue
                
            # Puliamo il titolo da eventuali tag HTML o spazi residui
            title = re.sub('<[^<]+?>', '', title_raw).strip()
            
            # Se il titolo estratto è vuoto o troppo corto, lo ricostruiamo leggendo lo slug dell'ID
            if not title:
                title = anime_id.split('-', 1)[-1].replace('-', ' ').title()

            if title and anime_id:
                if not any(r['id'] == anime_id for r in results):
                    results.append({
                        'title': title,
                        'id': anime_id
                    })

        # Se il server risponde vuoto a causa dei blocchi geografici o Cloudflare, 
        # restituiamo una lista fissa con dei titoli reali di test per verificare che la UI del 3DS sia sbloccata
        if not results:
            results.append({'title': 'One Piece (Test Sblocco)', 'id': '2549-demon-slayer'})
            results.append({'title': 'Naruto Shippuden (Test Sblocco)', 'id': '2549-demon-slayer'})
            results.append({'title': f"Nessun anime trovato sul sito per '{query}'", 'id': 'non-trovato'})

        return jsonify(results)
    except Exception as e:
        return jsonify([{
            'title': f"Errore Proxy: {str(e)[:20]}",
            'id': "errore-rete"
        }])

@app.route('/video')
def video():
    video_id = request.args.get('id', '')
    if not video_id or video_id in ["non-trovato", "errore-rete"]:
        return jsonify({'url': ''})

    try:
        url = f"{BASE_URL}/anime/{video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': BASE_URL
        }
        response = scraper.get(url, headers=headers, timeout=10)
        
        # Ricerca del file video diretto .mp4
        mp4_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', response.text)
        
        if mp4_match:
            video_url = mp4_match.group(1)
        else:
            # Fallback per i player embedded
            embed_match = re.search(r'src=["\'](https?://[^\s"\']+(?:embed|player)[^\s"\']*)["\']', response.text)
            if embed_match:
                iframe_res = scraper.get(embed_match.group(1), headers=headers, timeout=10)
                video_match = re.search(r'(https?://[^\s"\']+\.mp4[^\s"\']*)', iframe_res.text)
                video_url = video_match.group(1) if video_match else ""
            else:
                video_url = ""

        # Rimuoviamo l'HTTPS per aggirare le vecchie chiavi SSL del 3DS
        video_url_http = video_url.replace("https://", "http://")
        return jsonify({'url': video_url_http})
    except:
        return jsonify({'url': ''})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
