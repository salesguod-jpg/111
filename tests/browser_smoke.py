"""Optional browser smoke: pip install playwright==1.56.0; system chromium required."""
import functools, http.server, threading, json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT/'site')))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for width,height in [(1440,1000),(390,844)]:
        page=browser.new_page(viewport={'width':width,'height':height}); errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_selector('#list .empty')
        assert page.title()=='投资情报中心'
        assert page.locator('#topics button').count()==8
        page.locator('#theme').click();assert page.locator('body').evaluate('(el)=>el.classList.contains("dark")')
        page.locator('#search').fill('不存在的新闻');assert page.locator('#list .empty').count()==1
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), 'horizontal overflow'
        assert not errors,errors
        page.screenshot(path=f'/tmp/investment-hub-{width}.png',full_page=True)
        page.close()
    # Isolated test fixture, never saved as public news.
    page=browser.new_page(); fixture={'id':'fixture','original_title':'测试事件，非真实新闻','excerpt':'仅用于浏览器交互测试','published_at':'2026-10-28T01:00:00Z','collected_at':'2026-10-28T01:00:00Z','topics':['us'],'weight':7,'sources':[{'name':'Test','url':'https://example.org/'}],'analysis':None}
    index=json.loads((ROOT/'site/data/index.json').read_text());index['events']=[fixture]
    page.route('**/data/index.json',lambda route:route.fulfill(json=index))
    page.goto(f'http://127.0.0.1:{server.server_port}/');page.locator('#list h3 button').click();assert page.locator('dialog').is_visible();assert '无 AI 分析' in page.locator('#detail-body').inner_text()
    page.locator('#close').click();page.locator('#topics button',has_text='贵州茅台').click();assert page.locator('#list .empty').count()==1
    browser.close()
server.shutdown()
print('PASS: desktop/mobile loading, theme, search, topic, details, no overflow or JS errors')
