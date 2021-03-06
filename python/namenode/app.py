from flask import Flask, request, make_response, send_file
import os
import sys
import io
from random import randint
import hashlib
from cache import Cache
from namenode import *
import requests
from database import Database
from nodes import Nodes
import dedup as dedup
import gen_dedup as gen_dedup

BLOCK_SIZE = 1024

app = Flask(__name__)
nodes = Nodes()
cache = Cache()

node_id = os.environ.get("NODE_ID") if os.environ.get("NODE_ID") is not None else str(randint(0, 1000))
port = int(os.environ.get("PORT_NO")) if os.environ.get("PORT_NO") is not None else 3000
strategy = os.environ.get("STRATEGY") if os.environ.get("STRATEGY") is not None else "FULL_FILE"

print(f"Strategy: {strategy}.")

@app.route("/file_data", methods=["POST"])
def add_file_data():
    files = request.files
    file = files.get("file")
    file_data = bytearray(file.read())
    file_length = len(file_data)
    file_name = request.form.get("file_name")
    content_type = ".bin"

    save_file_data_and_metadata(file_data, file_name, file_length, content_type)
    return "", 200


@app.route("/file", methods=["POST"])
def add_file():
    files = request.files
    if not files or not files.get("file"):
        return make_response("File not found", 400)

    file = files.get("file")
    file_data = bytearray(file.read())
    file_length = len(file_data)
    content_type = file.mimetype
    save_file_data_and_metadata(file_data, file.filename, file_length, content_type)
    return "", 200


def save_file_data_and_metadata(file_data, file_name, file_length, content_type):
    if strategy == "FULL_FILE":
        pass
    elif strategy == "CODED":
        pass
    elif strategy == "DEDUP":
        dedup.save_file_data_and_metadata(file_data, file_name, file_length, content_type)
    elif strategy == "GEN_DEDUP":
        gen_dedup.save_file_data_and_metadata(file_data, file_name, file_length, content_type)

@app.route("/file/<filename>", methods=["GET"])
def get_file(filename):
    try:
        size, content_type, blocks, strategy = get_metadata(filename)
    except:
        return make_response("File does not exist", 404)

    if strategy == "FULL_FILE":
        pass
    elif strategy == "CODED":
        pass
    elif strategy == "DEDUP":
        file_data = dedup.get_file(filename, size, blocks)
    elif strategy == "GEN_DEDUP":
        file_data = gen_dedup.get_file(filename, size, blocks)

    return send_file(file_data, mimetype=content_type, as_attachment=True, attachment_filename=filename)


data_folder = sys.argv[1] if len(sys.argv) > 1 else "./files"

try:
    os.mkdir("./files")
except FileExistsError as _:
    # Folder exists
    pass

app.run(host="0.0.0.0", port=port)
