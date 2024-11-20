sometime the proxy have reachable website, i suggest to check before use it if you supposed to make web scraping:

while True:
  while True:
      response = proxy(db="./PROXY/proxy.db").proxy_request(self.url, timeout=8)
        if response:
          break

  info = BeautifulSoup(response.content, 'html.parser').get_info_with_xpath(xpath)
  
  if info is not None or info == []:
      break
