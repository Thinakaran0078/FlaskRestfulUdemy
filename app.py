import uuid
from flask import Flask, request
from flask_smorest import abort
from db import stores, items


app = Flask(__name__)

@app.route('/')
def index():
    return {"message": "Welcome to API page"}


@app.post("/store")
def create_store():
    store_data = request.get_json()
    if "name" not in store_data:
        abort(400, message="Ensure Store name is Present")
    for store in stores:
        if store["name"] == store_data["name"]:
            abort(400, message="Store already exists.")
    store_id = uuid.uuid4().hex
    store = {**store_data, "id": store_id}
    stores[store_id] = store

    return store


@app.post("/item")
def create_item():
    item_data = request.get_json()
    if(
        "price" not in item_data or "store_id" not in item_data or "name" not in item_data
    ):
        abort(400, message="Bad request. Ensure 'price', 'store_id', name are present.")
    for item in items.values():
        if (
            item_data["name"] == item["name"]
            and item_data["store_id"] == item["store_id"]
        ):
            abort(400, message="Item already exists.")

    if item_data["store_id"] not in stores:
        abort(404, message="Store not found.")

    item_id = uuid.uuid4().hex
    item = {**item_data, "id": item_id}
    items[item_id] = item

    return item


@app.get("/store/<string:store_id>")
def get_store(store_id):
    try:
        return stores[store_id]
    except KeyError:
        abort(404, message="Store not found.")

@app.get("/item/<string:item_id>")
def get_item(item_id):
    try:
        return items[item_id]
    except KeyError:
        abort(404, message="Item not found.")


@app.get("/store")
def get_stores():
    return {"stores": list(stores.values())}


@app.get("/item")
def get_all_items():
    return {"items": list(items.values())}