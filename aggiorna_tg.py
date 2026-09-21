import re
import requests
from bs4 import BeautifulSoup

# URL principali di RaiNews TGR Toscana
URLS = [
    "https://www.rainews.it/tgr/toscana/notiziari",
    "https://www.rainews.it/tgr/toscana"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
}

def cerca_flusso_video():
    for url in URLS:
        print(f"--> Tento la connessione a: {url}")
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            print(f"Stato risposta HTTP: {res.status_code}")
            
            # Cerca flussi diretti .m3u8 o .mp4
            videos = re.findall(r'https?://[^\s"<]+\.(?:m3u8|mp4)[^\s"<]*', res.text)
            if videos:
                print(f"Trovato flusso video diretto: {videos[0]}")
                return videos[0].replace("&amp;", "&")
            
            # Cerca link alle sottopagine delle edizioni
            soup = BeautifulSoup(res.text, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/tgr/toscana/" in href and any(x in href for x in ["video", "notiziari", "edizione"]):
                    if not href.startswith("http"):
                        href = "https://www.rainews.it" + href
                    links.append(href)
            
            print(f"Trovati {len(links)} link a possibili edizioni.")
            
            # Analizza le prime 5 pagine trovate
            for l in links[:5]:
                print(f"Ispeziono pagina edizione: {l}")
                page_res = requests.get(l, headers=HEADERS, timeout=10)
                v = re.findall(r'https?://[^\s"<]+\.(?:m3u8|mp4)[^\s"<]*', page_res.text)
                if v:
                    print(f"Flusso estratto da sotto-pagina: {v[0]}")
                    return v[0].replace("&amp;", "&")

        except Exception as e:
            print(f"Errore durante l'ispezione di {url}: {e}")

    return None

def main():
    stream_url = cerca_flusso_video()

    # Se la ricerca fallisce, usa il flusso streaming della diretta/differita regionale
    if not stream_url:
        print("ATTENZIONE: Estrazione automatica fallita. Imposto flusso di riserva TGR Toscana.")
        stream_url = "https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=tgr_toscana_m3u8"

    print(f"\nURL del flusso finale: {stream_url}\n")

    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-logo="https://www.rainews.it/assets/tgr-logo.png" group-title="TG Toscana", TG Toscana On Demand
{stream_url}
"""

    with open("tg_toscana.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("File tg_toscana.m3u8 generato e salvato!")

if __name__ == "__main__":
    main()
