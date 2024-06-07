import time
from flask import Flask, jsonify, request
import requests
import mysql.connector as connector
import logging as log

# region prepare

app = Flask(__name__)

logfile = 'dp_api.log'
log.basicConfig(filename=logfile, level=log.INFO)

process_timeout = {'timeout': 10,
                   'process': True}

mysql_service ='mysql_service'
# mysql_service ='localhost'
data_crawling = 'data_crawling'
# data_crawling = 'localhost'

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
    return {'error': 'error on request'} if process_timeout['process'] else req(url)

def connect_to_db():
    log.info('Connecting to database')
    db_config = { 
        'host': f'{mysql_service}',
        'port': '3306',
        'user': 'root',
        'password': 'psw123',
        'database': 'local_db'
    }
    for _ in range(20):
        try:
            conn = connector.connect(**db_config)
            log.info('Connected to database')
            return conn
        except connector.Error as e:
            log.error(e)
            log.info('Retrying...')
            time.sleep(5)
            
# endregion

# region main api
@app.route('/delete')
def delete_products():
    log.info('Deleting products')
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM products")
        connection.commit()
        cursor.close()
        connection.close()
        log.info('Products deleted')
        return {'result': "OK"}
    except connector.Error as e:
        log.error(e)
        return {"error": str(e)}

@app.route('/fetch')    
def fetch():
    log.info('Fetching data')
    products =  get_products_from_crawling()
    if 'error' in products:
        return products
    if len(products) == 0:
        e = 'No products'
        log.error(e)
        return {'error': e }
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM products")
        connection.commit()
        log.info('Products deleted')
        stmt = "INSERT INTO products (product_id, name, price, quantity, image) VALUES (%s, %s, %s, %s, %s)"
        data = []
        for product in products:
            data.append((product['product_id'], product['name'], product['price'], product['quantity'], product['image']))
        cursor.executemany(stmt, data)
        connection.commit()
        cursor.close()
        connection.close()
        log.info('Products fetched')
        return {'result': "OK"}
    except connector.Error as e:
        log.error(e)
        return {"error": str(e)}
    
@app.route('/products')
def get_products():
    log.info('Getting products')
    try:
        connection = connect_to_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM products")
        products = [{'product_id': product[0],
                     'name': product[1],
                     'price': product[2],
                     'quantity': product[3],
                     'image': product[4]} for product in cursor.fetchall()]
        cursor.close()
        connection.close()
        return products
    except connector.Error as e:
        log.error(e)
        return {"error": str(e)}
    
@app.route('/products/<search_query>')
def search_products(search_query):
    log.info(f'Searching for {search_query}')
    try:
        connection = connect_to_db()
        cursor = connection.cursor()       
        sql_query = "SELECT * FROM products WHERE name LIKE %s"
        cursor.execute(sql_query, ('%' + search_query + '%',))  
        products = [{'product_id': product[0],
                     'name': product[1],
                     'price': product[2],
                     'quantity': product[3],
                     'image': product[4]} for product in cursor.fetchall()]      
        cursor.close()
        connection.close()        
        return products
    except connector.Error as e:
        log.error(e)
        return {"error": str(e)}
# endregion

# region etc
@app.route('/')
def index():
    log.info('Hello to db_api!')
    return "Hello to db_api!"

@app.route('/timeout/<int:timeout>')
def set_process_timeout(timeout=0):
    log.info(f"Setting process timeout to {timeout} seconds")
    process_timeout['process'] = False if timeout == 0 else True
    process_timeout['timeout'] = timeout
    return f"Process timeout set to {timeout} seconds"

def get_products_from_crawling():
    log.info('Getting products from data_crawling')
    url = f'http://{data_crawling}:5000/crawling'
    products = req(url)
    url = f'http://{data_crawling}:5000/products'
    products = req(url)
    if products.get('products') is None: 
        return []
    else:
        return products['products']

@app.route('/log')
def get_log():
    with open(logfile, 'r') as f:
        return f.read().replace('\n', '<br>')

@app.route('/log/clear')
def clear_log():
    with open(logfile, 'w') as f:
        return 'Log cleared!'
    
@app.route("/demo")
def demo():
    log.info('Demo')
    search_query = 'Nữ'
    demo = { 
        "/" : index(),
        "/delete": delete_products(),
        "/fetch": fetch(),
        "/products": get_products(),
        f"/products/<{search_query}>": search_products(search_query),
    }
    return demo

# endregion
    
def main(host='0.0.0.0', port=5001):
    fetch()
    app.run(debug=True, host=host, port=port)
    
if __name__ == "__main__":
    # test()
    main()
    