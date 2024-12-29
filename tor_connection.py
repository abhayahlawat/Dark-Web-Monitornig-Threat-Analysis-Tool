from stem.control import Controller
from stem import Signal
import requests

def connect_to_tor():
    try:
        # Authenticate with the Tor control port
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password='your_password') 
            controller.signal(Signal.NEWNYM) 
        
        # Set up the requests session to use Tor
        session = requests.Session()
        session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050',
        }
        return session
    except Exception as e:
        print(f"Error connecting to Tor: {e}")
        return None
