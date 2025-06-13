from flask import Flask, render_template, request, jsonify
import requests
import threading
import time
from google.cloud import pubsub_v1
import json

app = Flask(__name__)

PROJECT_ID = "silent-octagon-460701-a0"
TOPIC_ID = "order-event"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

def publish_product_event(product_id, name, price):
    data = {
        "productId": product_id,
        "name": name,
        "price": price
    }
    print(f"Publishing to PubSub: {data}")
    # Pub/Sub expects bytes
    future = publisher.publish(topic_path, json.dumps(data).encode("utf-8"))
    message_id = future.result()
    print(f"Published message ID: {message_id}") 
    return message_id

shipping_progress = {}

def shipping_worker():
    while True:
        time.sleep(6000)  # Wait 10 minutes before processing all products
        for product_id in list(shipping_progress.keys()):
            if shipping_progress[product_id] > 0:
                shipping_progress[product_id] -= 1

# Start background thread
threading.Thread(target=shipping_worker, daemon=True).start()

@app.route('/', methods=['GET', 'POST'])
#def index():
    # if request.method == 'POST':
    #     data = request.get_json()
    #     product_id = data['product_id']
    #     name = data.get('name')
    #     price = data.get('price')
    #     shipping_progress[product_id] = shipping_progress.get(product_id, 0) + 1
    #     publish_product_event(product_id, name, price)
    #     return jsonify({
    #         "status": "success",
    #         "product_id": product_id,
    #         "shipping_in_progress": shipping_progress[product_id]
    #     })
       

    # resp = requests.get('https://product-backend-327554758505.us-central1.run.app/products')
    # products = resp.json()
    # orders = [
    #     {
    #         "product_id": p.get('product_id'),
    #         "product_name": p.get('name'),
    #         "shipping_in_progress": shipping_progress.get(p.get('product_id'), 0)
    #     }
    #     for p in products
    # ]
    # return render_template('index.html', orders=orders)

@app.route('/shipping_in_progress', methods=['GET'])
def get_shipping_in_progress():
    # Returns a list of dicts with product_id and shipping in progress
    result = [
        {"product_id": pid, "shipping_in_progress": count}
        for pid, count in shipping_progress.items()
    ]
    return jsonify(result)
@app.route('/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'POST':
        data = request.get_json()
        product_id = data['product_id']
        name = data.get('name')
        price = data.get('price')
        shipping_progress[product_id] = shipping_progress.get(product_id, 0) + 1
        publish_product_event(product_id, name, price)
        return jsonify({
            "status": "success",
            "product_id": product_id,
            "shipping_in_progress": shipping_progress[product_id]
        })
    resp = requests.get('https://product-backend-327554758505.us-central1.run.app/products')
    products = resp.json()
    orders = [
        {
            "product_id": p.get('product_id'),
            "product_name": p.get('name'),
            "shipping_in_progress": shipping_progress.get(p.get('product_id'), 0)
        }
        for p in products
    ]
    return render_template('index.html', orders=orders)



if __name__ == '__main__':
    app.run(debug=True, port=5004)