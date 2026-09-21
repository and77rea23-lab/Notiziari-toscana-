import re
import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.rainews.it/tgr/toscana/notiziari",
    "https://www.rainews.it/tgr/toscana"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.rainews.it/"
}

def cerca_flusso_video():
    for url in URLS:
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            
            videos = re.findall(r'https?://[^\s"<]+\.(?:m3u8|mp4)[^\s"<]*', res.text)
            if videos:
                return videos[0].replace("&amp;", "&")
            
            soup = BeautifulSoup(res.text, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/tgr/toscana/" in href and any(x in href for x in ["video", "notiziari", "edizione"]):
                    if not href.startswith("http"):
                        href = "https://www.rainews.it" + href
                    links.append(href)
            
            for l in links[:5]:
                page_res = requests.get(l, headers=HEADERS, timeout=10)
                v = re.findall(r'https?://[^\s"<]+\.(?:m3u8|mp4)[^\s"<]*', page_res.text)
                if v:
                    return v[0].replace("&amp;", "&")
        except Exception:
            pass

    return None

def main():
    stream_url = cerca_flusso_video()

    if not stream_url:
        stream_url = "https://mediapolis.rai.it/relinker/relinkerServlet.htm?cont=tgr_toscana_m3u8"

    # Intestazioni necessarie per superare il blocco Rai
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ref = "https://www.rainews.it/"
    
    # Formato M3U avanzato con parametri per TiviMate / OTT Navigator / VLC
    m3u_content = f"""#EXTM3U
#EXTVLCOPT:http-user-agent={ua}
#EXTVLCOPT:http-referrer={ref}
#EXTINF:-1 tvg-logo="https://www.rainews.it/assets/tgr-logo.png" http-user-agent="{ua}" http-referrer="{ref}", TG Toscana On Demand
{stream_url}|User-Agent={ua}&Referer={ref}
"""

    with open("tg_toscana.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print("File M3U aggiornato con header di protezione Rai!")

if __name__ == "__main__":
    main()
