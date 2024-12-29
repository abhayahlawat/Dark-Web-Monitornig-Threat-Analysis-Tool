from bs4 import BeautifulSoup

def scrape_onion_site(url, session):
    """Scrape the content of an onion site using a Tor session."""
    try:
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return None
