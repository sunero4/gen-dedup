import requests
import hashlib
from nodes import Nodes
from namenode import *
import io
from cache import Cache

nodes = Nodes()
cache = Cache()

BLOCK_SIZE = 1024
BASE_SIZE = 992

def save_file_data_and_metadata(file_data, file_name, file_length, content_type):
    existing, missing, new_blocks = create_blocks_and_hashes(file_data)
    
    block_node_assocations = {}

    for _, block_meta in missing.items():
        base_id = block_meta["base_id"]
        chunk = new_blocks[base_id]

        node_id = nodes.get_next_storage_node()
        requests.post(f"http://{node_id}/block", files=dict(block=chunk[:BASE_SIZE]), data=dict(block_name=base_id))

        if not base_id in block_node_assocations:
            block_node_assocations[base_id] = node_id
            save_block_node_association(base_id, node_id)


        block_meta["node_id"] = block_node_assocations[base_id]

    block_dic = existing | missing

    save_metadata(file_name, file_length, content_type, block_dic, "GEN_DEDUP")

def create_block_hash_and_deviation(block):
    base = block[:BASE_SIZE]
    deviation = block[BASE_SIZE:]

    print(f"base len: {len(base)}")
    print(f"dev len: {len(deviation)}")

    md5_hash = hashlib.md5(base)
    base_id = md5_hash.digest().hex()

    return base_id, deviation


def create_blocks_and_hashes(file_data):
    existing, missing, new_blocks = {}, {}, {}

    chunks = [file_data[i:i+BLOCK_SIZE] for i in range(0, len(file_data), BLOCK_SIZE)]

    for count, chunk in enumerate(chunks):
        base_id, deviation = create_block_hash_and_deviation(chunk)

        node_id = get_block_storage_node(base_id)

        if not node_id:
            missing[count] = {'base_id': base_id, 'node_id': node_id, 'deviation': bytes(deviation).hex()}
            new_blocks[base_id] = chunk
        else:
            print(f"block with id: {base_id} exists already.")
            existing[count] = {'base_id': base_id, 'node_id': node_id, 'deviation': bytes(deviation).hex()}

    return existing, missing, new_blocks


def get_file(filename, size, blocks):
    file_blocks = [None] * len(blocks.keys())

    for order, block_meta in blocks.items():
        base_id = block_meta["base_id"]
        node_id = block_meta["node_id"]
        deviation_hex = block_meta["deviation"]
        deviation = bytearray.fromhex(deviation_hex)

        cache_val = cache.get_from_cache(base_id)
        if cache_val is not None:
            print("hit cache", flush=True)
            file_blocks[int(order)] = cache_val + deviation
            print(f"len: {len(cache_val)}, {len(deviation)}")
        else:
            print("not in cache", flush=True)
            req = requests.get(f"http://{node_id}/block/{base_id}")
            block_val = req.content
            cache.add_to_cache(base_id, block_val)
            print(f"len: {len(block_val)}, {len(deviation)}")

            file_blocks[int(order)] = block_val + deviation

    file = b"".join(file_blocks)
    return io.BytesIO(file)

    # return send_file(io.BytesIO(file), mimetype=content_type, as_attachment=True, attachment_filename=filename)