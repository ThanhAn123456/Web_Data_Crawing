import threading
from flask import Flask
import requests
import schedule
import time
import logging as log


# region prepare
app = Flask(__name__)

logfile = 'data_crawling.log'
log.basicConfig(filename=logfile, format='%(asctime)s - %(levelname)s - %(message)s', level=log.INFO)

process_timeout = {'timeout': 10,
                   'process': True}

config = {
    'at_day': [],
    'at_hour': [],
    'anytime': {
        'freq': 1,
        'unit': 'minutes'
    },
    'mode': 'anytime'
}

def schedule_crawling():
    schedule.clear()  # Clear existing scheduled jobs
    if config['mode'] == 'at_day':
        for time_str in config['at_day']:
            schedule.every().day.at(time_str).do(fetch)
    elif config['mode'] == 'at_hour':
        for time_str in config['at_hour']:
            schedule.every().hour.at(time_str).do(fetch)
    elif config['mode'] == 'anytime':
        freq = config['anytime']['freq'] 
        unit = config['anytime']['unit']
        if unit == 'minutes':
            schedule.every(freq).minutes.do(fetch)
        elif unit == 'hours':
            schedule.every(freq).hours.do(fetch)
        elif unit == 'days':
            schedule.every(freq).days.do(fetch)


def run_schedule():
    global is_running
    is_running = True
    while is_running:
        schedule.run_pending()
        time.sleep(1)

        
@app.route('/schedule/stop')
def stop_schedule():
    global is_running
    is_running = False
    return 'Schedule stopped'

@app.route('/schedule/start')
def start_schedule():
    run_schedule()
    return 'Schedule started'

@app.route('/schedule/check')
def check_schedule():
    global is_running
    return {'running': is_running}
        
@app.route('/schedule/<mode>/<datetime>')
def set_schedule(mode='at_day', datetime='00:00'):
    config['mode'] = mode
    if mode == 'at_day':
        config['at_day'].append(str(datetime))
    elif mode == 'at_hour':
        config['at_hour'].append(str(datetime))
    schedule_crawling()
    return config
        
@app.route('/schedule/anytime/<int:freq>/<unit>')
def set_freq(freq=1, unit='minutes'):
    config['mode'] = 'anytime'
    config['anytime'] = {'freq': freq, 'unit': unit}
    schedule_crawling()
    return config

def req(url):
    log.info(f"Requesting {url}")
    try:
        res = requests.get(url, timeout=process_timeout['timeout'])
        if res.status_code == 200:
            return res.json() if res is not None else req(url)
    except requests.Timeout:
        log.error("Request timed out")
    except requests.RequestException as e:
        log.error(f"Request failed: {e}")
    return {'data': []} if process_timeout['process'] else req(url)

# endregion

# region main api

@app.route('/crawling')
def craw():
    log.info('Crawling data')
    res1 = req("https://recommend-api.sendo.vn/web/listing/recommend/internal?track_id=06e0e029-b875-4764-8d54-e0ac6570928e&p=1&s=100&cate_path=thoi-trang-nu&sort_type=vasup_desc&platform=desktop2&app_verion=2.39.3&session_key=1714816781570&version=v2&is_new_listing=2")
    data1 = res1['data']
    res2 = req("https://recommend-api.sendo.vn/web/listing/recommend/internal?track_id=144a92b2-3f9f-482e-b1a7-b12b478ac937&p=1&s=100&cate_path=quat&sort_type=vasup_desc&platform=desktop2&app_verion=2.39.3&session_key=1714839580730&version=v2&is_new_listing=2")
    data2 = res2['data']
    res3 = req("https://recommend-api.sendo.vn/web/listing/recommend/internal?track_id=144a92b2-3f9f-482e-b1a7-b12b478ac937&p=1&s=100&cate_path=thiet-bi-cham-soc-quan-ao&sort_type=vasup_desc&platform=desktop2&app_verion=2.39.3&session_key=1714840565419&version=v2&is_new_listing=2")
    data3 = res3['data']
    data = data1 + data2 + data3
    seen_ids = set()
    global products
    products = []
    for product in data:
        if 'is_empty' not in product:
            product_id = product['item']['product_id']
            product_name = product['item']['name']
            
            # Kiểm tra tính hợp lệ của tên sản phẩm
            if product_id not in seen_ids and ('𝑭𝑹𝑬𝑬𝑺𝑯𝑰𝑷' not in product_name):
                products.append({
                    'product_id': product_id,
                    'name': product_name,
                    'price': product['item']['price'],
                    'quantity': product['item']['quantity'] if 'quantity' in product['item'] else 1,
                    'image': product['item']['thumbnail_url']
                })
                seen_ids.add(product_id)
    return { 'result': "OK" if len(products) > 0 else "FAIL" }

@app.route('/fetch')
def fetch():
    log.info('Fetching data ')
    url = 'http://db_api:5001/fetch'
    res = req(url)
    return res

@app.route('/products')
def get_products():
    log.info('Getting products')
    return {'products': products}

@app.route('/quantity')
def get_quantity():
    log.info('Getting quantity')
    return {'quantity': len(products)}

# endregion

# region etc

@app.route('/timeout/<int:timeout>')
def set_process_timeout(timeout=0):
    log.info(f"Setting process timeout to {timeout} seconds")
    process_timeout['process'] = False if timeout == 0 else True
    process_timeout['timeout'] = timeout
    return f"Process timeout set to {timeout} seconds"

@app.route('/')
def index():
    log.info('Hello to Data_crawling!')
    return "Hello to Data_crawling!"

@app.route('/demo')
def demo():
    log.info('Demo')
    global products
    demo = {'/': index(),
            '/crawling': craw(),
            '/quantity': get_quantity(),
            '/products': products}
    return demo

def crawling(url):
    response = req(url)
    data = response.json()['data']
    return data

@app.route('/log')
def get_log():
    with open(logfile, 'r') as f:
        return f.read().replace('\n', '<br>')

@app.route('/log/clear')
def clear_log():
    with open(logfile, 'w') as f:
        return 'Log cleared!'
     
# endregion

def main(host='0.0.0.0', port=5000):
    log.info('Starting data_crawling')
    global products
    products = []
    craw()
    schedule_crawling()
    schedule_thread = threading.Thread(target=run_schedule)
    schedule_thread.start()
    app.run(host=host, port=port)
    
if __name__ == "__main__":
    #    test()
    main()
