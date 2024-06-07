import logging as log
from flask import Flask, render_template
import requests

# region prepare

app = Flask(__name__)

logfile = 'web.log'
log.basicConfig(filename=logfile, level=log.INFO)

db_api = 'db_api'
# db_api = 'localhost'

process_timeout = {'timeout': 5,
                   'process': True}

def req(url):
    log.info(f"Requesting {url}")
    try:
        res = requests.get(url, timeout=process_timeout['timeout'])
        if res.status_code == 200:
            return res if res is not None else req(url)
    except requests.Timeout:
        log.error("Request timed out")
    except requests.RequestException as e:
        log.error(f"Request failed: {e}")
    return {'error': 'error on request'} if process_timeout['process'] else req(url)

# endregion

# region main api

@app.route('/api/products/<search_query>')
def search(search_query = ''):
    log.info('Getting products')
    fetch()
    url = f'http://{db_api}:5001/products/{search_query}'
    products = req(url).json()
    return products

@app.route('/api/products')
def get_products():
    log.info('Getting products')
    fetch()
    url = f'http://{db_api}:5001/products'
    products = req(url).json()
    return products


@app.route('/fetch')
def fetch():
    log.info('Fetching data')
    # url = f'http://{db_api}:5001/fetch'
    # res = req(url).json()
    # return res
    return None
# endregion

# region etc

@app.route('/timeout/<int:timeout>')
def set_process_timeout(timeout=0):
    log.info(f"Setting process timeout to {timeout} seconds")
    process_timeout['process'] = False if timeout == 0 else True
    process_timeout['timeout'] = timeout
    return f"Process timeout set to {timeout} seconds"

@app.route('/')
def home():
    log.info('Home')
    return render_template('index.html')

@app.route('/log')
def get_log():
    with open(logfile, 'r') as f:
        return f.read().replace('\n', '<br>')

@app.route('/log/clear')
def clear_log():
    with open(logfile, 'w') as f:
        return 'Log cleared!'

# endregion

def main(host='0.0.0.0', port=3000):
    log.info('Starting web')
    app.run(debug=True, host=host, port=port)
    
if __name__ == "__main__":
    main()
