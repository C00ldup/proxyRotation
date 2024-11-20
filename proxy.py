import requests
import re
import sqlite3
import ast
import random
import os
from requests.exceptions import ProxyError, RequestException
from fake_useragent import UserAgent

class hideIP:
    def __init__(self) -> None:
        pass
    
    def new_user_agent(self) -> dict:
        headers = { 'User-Agent' : UserAgent().random,
                    'Accept' : 'application/json, text/plain, */*',
                    'Accept-Encoding' : 'gzip, deflate, br, zstd',
                    'Accept-Language' : 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
                    'Connection' : 'keep-alive',
                    'Sec-Fetch-Dest' : 'empty',
                    'Sec-Fetch-Mode' : 'cors',
                    'Sec-Fetch-Site' : 'same-origin',
                }
        return headers

#print(hideIP().new_user_agent())

class proxy():
    def __init__(self, db) -> None:
        self.db = os.path.join(os.path.dirname(__file__), db)
        self.myIP = requests.get('http://ifconfig.me/').text
    
    def get_new_proxy_list(self, proxy_dict={}, headers=hideIP().new_user_agent()):
        site = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        response = requests.get(site, proxies=proxy_dict, headers=headers)
        return response.text.splitlines()
    
    def try_proxy(self, proxy_list=[], verbose=False, save_proxy=False):
        proxy_types = [
            'http',  # HTTP proxy
            'https',  # HTTPS proxy
            'socks5',  # SOCKS5 proxy
        ]
        for proxy_type in proxy_types:
            for proxy in proxy_list:
                proxy_dict = {proxy_type: proxy_type + "://" + proxy}
                #print(proxy_dict)
                try:
                    #response = requests.get('http://httpbin.org/ip', proxies=proxy_dict, timeout=2, headers=hideIP().new_user_agent())
                    #ip = response.json()['origin']
                    response = requests.get('http://api.ipify.org/?format=json', proxies=proxy_dict, timeout=2, headers=hideIP().new_user_agent())
                    ip = response.json()['ip']
                    
                    #ip_location = requests.get(f'http://ip-api.com/json/{ip}', proxies=proxy_dict, timeout=2, headers=hideIP().new_user_agent()).json()
                    #ip_location = requests.get(f'http://freeipapi.com/api/json/{ip}', proxies=proxy_dict, timeout=2, headers=hideIP().new_user_agent()).json()
                    #print(ip_location)
                    
                    if re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", ip) and ip != self.myIP:
                        response = requests.get('http://ifconfig.me/', proxies=proxy_dict, timeout=2)
                        if re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", response.text):
                            if verbose:
                                print([proxy_type, proxy, proxy_type + "://" + proxy, proxy_dict, response.text])
                                
                            if save_proxy:
                                self.db_save([proxy_type, proxy, proxy_type + "://" + proxy, proxy_dict, response.text])
                            else:
                                return proxy_dict
                except requests.exceptions.RequestException as e:
                    #print(f"Failed with {proxy_type} proxy: {e}")
                    continue
                except requests.exceptions.Timeout:
                    #print("Request timed out.")
                    continue
                except requests.exceptions.RequestException as e:
                    #print(f"Request failed: {e}")
                    continue
    
    def db_save(self, data=[]):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proxy (
                id INTEGER PRIMARY KEY,
                full_address TEXT UNIQUE,
                proxy_type TEXT,
                proxy_address TEXT,
                proxy_dict TEXT,
                showed_ip TEXT
            )
        """)
        
        cursor.execute("SELECT COUNT(*) FROM proxy WHERE full_address = ?", (data[2],))
        existing = cursor.fetchone()[0]
        
        if existing == 0:
            cursor.execute("INSERT INTO proxy (full_address, proxy_type, proxy_address, proxy_dict, showed_ip) \
                        VALUES (?, ?, ?, ?, ?)", (str(data[2]), str(data[0]), str(data[1]), str(data[3]), str(data[4])))

            conn.commit()

            cursor.execute("SELECT * FROM proxy")
            rows = cursor.fetchall()

            '''for row in rows:
                print(row)'''

            conn.close()
            
            print("Uploaded: {}".format(str(data[2])))
    
    def db_random_proxy(self):
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT proxy_dict FROM proxy")
        results = [ast.literal_eval(row[0]) for row in cursor.fetchall()]
        
        return random.choice(results)
    
    def get_proxy_schema(self, url, proxy):
        if not re.search(r'^http', url):
            conn = sqlite3.connect(self.db)
            cursor = conn.cursor()
            cursor.execute("SELECT proxy_type FROM proxy WHERE proxy_dict = ?", (str(proxy),))
            rows = cursor.fetchall()
            results = [row[0] for row in rows]
            return results[0] + "://" + url
        else:
            return url
    
    def proxy_request(self, url, timeout=2):
        proxy = self.db_random_proxy()
        url = self.get_proxy_schema(url, proxy)
        
        print(f"\r\033[K{Color().color_text('Trying', Color.RED)} {proxy['http']} on {url}", end='', flush=True)
        
        try:
            response = requests.get(url, proxies=proxy, headers=hideIP().new_user_agent(), timeout=timeout)
            response.raise_for_status()
            print(f'\n{Color().color_text(f'OK {response.url}', Color.GREEN)}')
            return response
        except ProxyError as e:
            return self.proxy_request(url, timeout)

        except RequestException as e:
            # todo captcha solver
            return self.proxy_request(url, timeout)

        except Exception as e:
            return self.proxy_request(url, timeout)
        
'''
supported list type:
ip:port

store proxy:
proxy = proxy(db="./proxy.db")
while True:
    proxy.try_proxy(proxy.get_new_proxy_list(proxy_dict=proxy.db_random_proxy()), save_proxy=True)
    
use proxy:
proxy(db="./proxy.db").proxy_request(self.url, timeout=8)

-> return a requests response

get random proxy to use in a request
proxy(db="./proxy.db").db_random_proxy()

get new proxy from online list
proxy.try_proxy(proxy.get_new_proxy_list(proxy_dict=proxy.db_random_proxy()))
'''

class Color:
    # ANSI Escape Codes for text and background colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    # Colors (foreground)
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Background colors
    BACK_BLACK = '\033[40m'
    BACK_RED = '\033[41m'
    BACK_GREEN = '\033[42m'
    BACK_YELLOW = '\033[43m'
    BACK_BLUE = '\033[44m'
    BACK_MAGENTA = '\033[45m'
    BACK_CYAN = '\033[46m'
    BACK_WHITE = '\033[47m'

    @staticmethod
    def color_text(text, color=None, bg_color=None, style=None, bold=False, underline=False):
        """
        Apply color and style to the text.
        Arguments:
        - text: The text to be colored.
        - color: The foreground color.
        - bg_color: The background color.
        - style: The style (e.g., bold, underline).
        - bold: Boolean to apply bold style.
        - underline: Boolean to apply underline style.
        """
        styles = []
        if bold: styles.append(Color.BOLD)
        if underline: styles.append(Color.UNDERLINE)
        
        color_code = color if color else ''
        bg_color_code = bg_color if bg_color else ''
        style_code = ''.join(styles)

        return f"{style_code}{color_code}{bg_color_code}{text}{Color.RESET}"

'''
if __name__ == "__main__":
    color = Color()

    print(color.color_text("This is bold and underlined red text", Color.RED, None, None, bold=True, underline=True))
    print(color.color_text("This is green text with blue background", Color.GREEN, Color.BACK_BLUE))
    print(color.color_text("Text with yellow background and bold style", None, Color.BACK_YELLOW, None, bold=True))
'''
