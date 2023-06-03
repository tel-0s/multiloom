from flask import Flask, request, jsonify
import sqlite3
import threading
import uuid
import dotenv
import os
import hashlib
import json
import time

app = Flask(__name__)

# Load the environment variables
dotenv.load_dotenv()
TREE_FILE = os.getenv('TREE_FILE')
TREE_JSON = os.getenv('TREE_JSON')
SERVER_PASSWORD_HASH = hashlib.sha256(os.getenv('SERVER_PASSWORD').encode()).hexdigest()
SERVER_PORT = os.getenv('SERVER_PORT')

# If TREE_JSON is specified, delete the existing database
if TREE_JSON:
    if os.path.exists(TREE_JSON):
        # Delete the existing database
        if os.path.exists(TREE_FILE):
            os.remove(TREE_FILE)

# Create the nodes table
conn = sqlite3.connect(TREE_FILE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS nodes
             (id TEXT PRIMARY KEY,
              parent_ids TEXT,
              text TEXT,
              author TEXT,
              timestamp TEXT)''')
conn.commit()
conn.close()

# If TREE_JSON exists, load it into the database
if TREE_JSON:
    if os.path.exists(TREE_JSON):
        with open(TREE_JSON) as f:
            tree_json = json.load(f)
            # print(tree_json)

            # get current timestamp
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            conn = sqlite3.connect(TREE_FILE)
            c = conn.cursor()
            for node in tree_json['nodes']:
                node_data = tree_json['nodes'][node]
                # get parent id(s)
                if 'parentIds' in node_data:
                    parent_ids = ','.join(node_data['parentIds'])
                else:
                    parent_ids = node_data['parentId']
                c.execute("INSERT INTO nodes (id, parent_ids, text, author, timestamp) VALUES (?, ?, ?, ?, ?)",
                            (node, parent_ids, node_data['text'], "Morpheus", timestamp))
            conn.commit()
            conn.close()

# Define a function to check if a user is authorized to make changes to the database
def is_authorized(key):
    # Check if the key is valid
    if hashlib.sha256(key.encode()).hexdigest() == SERVER_PASSWORD_HASH:
        return True
    else:
        return False

# Define a function to create a new connection and cursor object
def get_db():
    if not hasattr(threading.current_thread(), 'sqlite_db'):
        threading.current_thread().sqlite_db = sqlite3.connect('tree.db')
    return threading.current_thread().sqlite_db, threading.current_thread().sqlite_db.cursor()

# Define a function to close the connection when the request is finished
@app.teardown_appcontext
def close_db(error):
    if hasattr(threading.current_thread(), 'sqlite_db'):
        threading.current_thread().sqlite_db.close()

# Define a route for saving a new node to the database
@app.route('/nodes', methods=['POST'])
def save_node():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    db, c = get_db()
    data = request.get_json()
    # get parent id(s)
    if 'parentIds' in data:
        parent_ids = ','.join(data['parentIds'])
    else:
        parent_ids = data['parentId']
    text = data['text']
    author = data['author']
    timestamp = data['timestamp']
    # generate a new id for the node
    node_id = uuid.uuid4().hex
    c.execute("INSERT INTO nodes (id, parent_ids, text, author, timestamp) VALUES (?, ?, ?, ?, ?)",
                (node_id, parent_ids, text, author, timestamp))
    db.commit()
    return jsonify({'success': True})

# Define a route for updating an existing node in the database
@app.route('/nodes/<node_id>', methods=['PUT'])
def update_node(node_id):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    db, c = get_db()
    data = request.get_json()
    text = data['text']
    author = data['author']
    timestamp = data['timestamp']
    c.execute("UPDATE nodes SET text = ?, author = ?, timestamp = ? WHERE id = ?",
              (text, author, timestamp, node_id))
    db.commit()
    return jsonify({'success': True})

# Define a route for deleting a node from the database
@app.route('/nodes/<node_id>', methods=['DELETE'])
def delete_node(node_id):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    db, c = get_db()
    c.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    db.commit()
    return jsonify({'success': True})

# Define a route for getting all nodes from the database after a given timestamp
@app.route('/nodes/get/<timestamp>', methods=['GET'])
def get_nodes(timestamp):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes WHERE timestamp > ?", (timestamp,))
    nodes = c.fetchall()
    # jsonify the nodes
    nodes = [{
        'id': node[0],
        'parent_ids': node[1].split(',') if node[1] else None,
        'text': node[2],
        'author': node[3],
        'timestamp': node[4]
    } for node in nodes]
    return jsonify({'success': True, 'nodes': nodes})

# Define a route for getting all nodes from the database
@app.route('/nodes', methods=['GET'])
def get_all_nodes():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes")
    nodes = c.fetchall()
    # jsonify the nodes
    nodes = [{
        'id': node[0],
        'parent_ids': node[1].split(',') if node[1] else None,
        'text': node[2],
        'author': node[3],
        'timestamp': node[4]
    } for node in nodes]
    return jsonify({'success': True, 'nodes': nodes})

# Define a route for getting a single node from the database
@app.route('/nodes/<node_id>', methods=['GET'])
def get_node(node_id):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
    node = c.fetchone()
    # jsonify the node
    node = {
        'id': node[0],
        'parent_ids': node[1].split(',') if node[1] else None,
        'text': node[2],
        'author': node[3],
        'timestamp': node[4]
    }
    return jsonify({'success': True, 'node': node})

# Define a route for getting the root node from the database
@app.route('/nodes/root', methods=['GET'])
def get_root_node():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes WHERE parent_ids IS NULL")
    node = c.fetchone()
    # jsonify the node
    node = {
        'id': node[0],
        'parent_ids': None,
        'text': node[2],
        'author': node[3],
        'timestamp': node[4]
    }
    return jsonify({'success': True, 'node': node})

app.run(port=SERVER_PORT, debug=True)