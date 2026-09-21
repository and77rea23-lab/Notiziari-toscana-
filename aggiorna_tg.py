import re
import requests
from bs4 import BeautifulSoup

URLS = [
    "https://www.rainews.it/tgr/toscana/notiziari",
    "https://www.rainews.it/tgr/toscana"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
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
                if "/tgr/toscana/" in href and any(x in href.lower() for x in ["video", "notiziari", "edizione"]):
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

    # Genera un file M3U pulito e compatibile al 100% con Televizo
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-logo="https://www.rainews.it/assets/tgr-logo.png" group-title="TG Toscana", TG Toscana On Demand
{stream_url}
"""

    with open("tg_toscana.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"File M3U pulito salvato con successo! URL: {stream_url}")

if __name__ == "__main__":
    main()
