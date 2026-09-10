import requests
from lxml import html
HEADERS={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Test contact@test.com'}
url='https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets'
r=requests.get(url, headers=HEADERS, timeout=30)
print('status', r.status_code)
tree=html.fromstring(r.text)
xp1='/html/body/main/div[2]/div/div/div/div[1]/div/div[2]/div[4]/div/div/div/div/table/tbody/tr[1]/td[1]/a'
xpall='/html/body/main/div[2]/div/div/div/div[1]/div/div[2]/div[4]/div/div/div/div/table/tbody/tr/td[1]/a'
xpf='//table//tr/td[1]/a[contains(@href, ".zip")]'
a1=tree.xpath(xp1)
print('xp1 len', len(a1))
if a1:
    print('xp1 href', a1[0].get('href'))
    print('xp1 text', a1[0].text_content().strip())
print('xpall len', len(tree.xpath(xpall)))
print('xpf len', len(tree.xpath(xpf)))
for a in tree.xpath(xpf)[:5]:
    print(a.text_content().strip(), '->', a.get('href'))
