import re
import requests
from bs4 import BeautifulSoup

# Pagina principale notiziari TGR Toscana
NOTIZIARI_URL = "https://www.rainews.it/tgr/toscana/notiziari"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def main():
    print("Connessione alla pagina notiziari TGR Toscana...")
    res = requests.get(NOTIZIARI_URL, headers=HEADERS, timeout=15)
    res.raise_for_status()

    # Cerca il link della prima edizione disponibile
    matches = re.findall(r'href="(/tgr/toscana/notiziari/video/[^"]+)"', res.text)
    if not matches:
        matches = re.findall(r'href="(https://www.rainews.it/tgr/toscana/notiziari/video/[^"]+)"', res.text)

    if not matches:
        raise ValueError("Nessuna edizione trovata nella pagina.")

    last_edition_url = matches[0]
    if not last_edition_url.startswith("http"):
        last_edition_url = "https://www.rainews.it" + last_edition_url

    print(f"Ultima edizione trovata: {last_edition_url}")

    # Estrazione del flusso video dalla pagina dell'edizione
    page_res = requests.get(last_edition_url, headers=HEADERS, timeout=15)
    page_res.raise_for_status()

    # Cerca flussi m3u8 o mp4
    video_urls = re.findall(r'https?://[^\s"<]+\.(?:m3u8|mp4)[^\s"<]*', page_res.text)

    if not video_urls:
        soup = BeautifulSoup(page_res.text, "html.parser")
        og_video = soup.find("meta", property="og:video")
        if og_video and og_video.get("content"):
            video_urls = [og_video["content"]]

    if not video_urls:
        raise ValueError("Flusso video non trovato nella pagina dell'edizione.")

    stream_url = video_urls[0]
    print(f"Flusso video estratto: {stream_url}")

    # Scrittura della playlist M3U
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-logo="https://www.rainews.it/assets/tgr-logo.png" group-title="TG Toscana", TG Toscana On Demand
{stream_url}
"""

    with open("tg_toscana.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("File tg_toscana.m3u8 aggiornato con successo!")

if __name__ == "__main__":
    main()
