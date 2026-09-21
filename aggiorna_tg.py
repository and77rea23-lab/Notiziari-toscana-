import re
import requests
from bs4 import BeautifulSoup

TARGET_URLS = [
    "https://www.rainews.it/tgr/toscana/notiziari",
    "https://www.rainews.it/tgr/toscana"
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    )
}

def get_stream_url():
    for url in TARGET_URLS:
        print(f"Connessione a {url}...")
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            res.raise_for_status()
        except Exception as e:
            print(f"Errore connessione a {url}: {e}")
            continue

        # 1. Cerca direttamente se c'è un file m3u8 o mp4 nella pagina
        direct_videos = re.findall(r'https?://[^\s"<]+\.(?:m3u8|mp4)[^\s"<]*', res.text)
        if direct_videos:
            return direct_videos[0].replace("&amp;", "&")

        # 2. Cerca link alle edizioni video (pattern flessibile)
        soup = BeautifulSoup(res.text, "html.parser")
        edition_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/tgr/toscana/" in href and any(k in href.lower() for k in ["video", "notiziari", "edizione", "articolo"]):
                if not href.startswith("http"):
                    href = "https://www.rainews.it" + href
                edition_links.append(href)

        if not edition_links:
            raw_matches = re.findall(r'href="(/tgr/toscana/[^"]+)"', res.text)
            for m in raw_matches:
                if not m.startswith("http"):
                    m = "https://www.rainews.it" + m
                edition_links.append(m)

        # Analizza i link trovati per estrarre il video
        for ed_link in edition_links[:10]:
            print(f"Analizzo edizione: {ed_link}")
            try:
                page_res = requests.get(ed_link, headers=HEADERS, timeout=10)
                page_res.raise_for_status()
                
                v_urls = re.findall(r'https?://[^\s"<]+\.(?:m3u8|mp4)[^\s"<]*', page_res.text)
                if v_urls:
                    return v_urls[0].replace("&amp;", "&")
                
                p_soup = BeautifulSoup(page_res.text, "html.parser")
                og_vid = p_soup.find("meta", property="og:video")
                if og_vid and og_vid.get("content"):
                    return og_vid["content"].replace("&amp;", "&")
            except Exception as e:
                print(f"Errore caricamento {ed_link}: {e}")

    raise ValueError("Impossibile reperire il flusso video dell'ultima edizione.")

def main():
    stream_url = get_stream_url()
    print(f"\nFlusso video estratto con successo:\n{stream_url}\n")

    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-logo="https://www.rainews.it/assets/tgr-logo.png" group-title="TG Toscana", TG Toscana On Demand
{stream_url}
"""
    with open("tg_toscana.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("File tg_toscana.m3u8 salvato correttamente!")

if __name__ == "__main__":
    main()
