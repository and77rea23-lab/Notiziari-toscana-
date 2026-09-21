import re
import requests

BASE_URL = "https://www.rainews.it/tgr/toscana/notiziari"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
}

def pulisci_url(url):
    """Pulisce l'URL rimuovendo caratteri di escaping JSON e aggiunge il dominio se relativo."""
    if not url:
        return ""
    url = url.replace("\\/", "/").replace("&amp;", "&").strip('"\'')
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/") and not url.startswith("http"):
        url = "https://www.rainews.it" + url
    return url

def risolvi_relinker(url):
    """Segue i reindirizzamenti dei server Rai per ottenere l'URL finale diretto .m3u8 o .mp4."""
    try:
        r = requests.get(url, headers=HEADERS, allow_redirects=True, stream=True, timeout=10)
        return r.url
    except Exception as e:
        print(f"Errore risoluzione reindirizzamento per {url}: {e}")
        return url

def cerca_flusso_video():
    print(f"Connessione a {BASE_URL}...")
    res = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    res.raise_for_status()

    # Cerca tutti i possibili percorsi TGR Toscana nel sorgente (anche in blocchi JSON)
    pattern_tgr = r'\/tgr\/toscana\/[a-zA-Z0-9_\-\/]+'
    trovati = re.findall(pattern_tgr, res.text)
    
    link_edizioni = []
    for l in trovati:
        url_pulito = pulisci_url(l)
        if url_pulito not in link_edizioni and any(k in url_pulito for k in ["video", "notiziari", "edizione", "articoli"]):
            link_edizioni.append(url_pulito)

    print(f"Trovati {len(link_edizioni)} link ad edizioni TGR.")

    # Ispeziona le pagine trovate per estrarre il video
    for ed_url in link_edizioni[:10]:
        print(f"Ispeziono la pagina: {ed_url}")
        try:
            page_res = requests.get(ed_url, headers=HEADERS, timeout=10)
            page_text = page_res.text

            # Cerca flussi diretti .m3u8 o .mp4
            videos = re.findall(r'https?:\\?/\\?/[^\s"<>]+\.(?:m3u8|mp4)[^\s"<>]*', page_text)
            if not videos:
                # Cerca relinker Rai
                videos = re.findall(r'https?:\\?/\\?/[^\s"<>]*relinker[^\s"<>]*', page_text)
            if not videos:
                # Cerca meta tag contentUrl / og:video
                videos = re.findall(r'"contentUrl"\s*:\s*"([^"]+)"', page_text)

            if videos:
                raw_video_url = pulisci_url(videos[0])
                print(f"Individuato link video grezzo: {raw_video_url}")
                
                # Risolve l'URL finale seguendo i redirect dei server Rai
                final_stream = risolvi_relinker(raw_video_url)
                print(f"Flusso finale risolto: {final_stream}")
                return final_stream

        except Exception as e:
            print(f"Errore durante la lettura di {ed_url}: {e}")

    # Fallback: cerca m3u8 diretti nella pagina principale
    direct_videos = re.findall(r'https?:\\?/\\?/[^\s"<>]+\.(?:m3u8|mp4)[^\s"<>]*', res.text)
    if direct_videos:
        return risolvi_relinker(pulisci_url(direct_videos[0]))

    raise ValueError("Nessun flusso video trovato nella pagina dei notiziari Rai.")

def main():
    stream_url = cerca_flusso_video()

    print(f"\nFlusso video estratto con successo:\n{stream_url}\n")

    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-logo="https://www.rainews.it/assets/tgr-logo.png" group-title="TG Toscana", TG Toscana On Demand
{stream_url}
"""

    with open("tg_toscana.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("File tg_toscana.m3u8 aggiornato e salvato con successo!")

if __name__ == "__main__":
    main()
