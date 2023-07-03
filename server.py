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
TREE_ID = os.getenv('TREE_ID')
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
              children_ids TEXT,
              text TEXT,
              author TEXT,
              timestamp TEXT)''')
conn.commit()
conn.close()

# Create the history table (just node ids, timestamps, and operations)
conn = sqlite3.connect(TREE_FILE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS history
             (id TEXT PRIMARY KEY,
              timestamp TEXT,
              operation TEXT,
              author TEXT)''')

# If TREE_JSON exists, load it into the database
if TREE_JSON:
    if os.path.exists(TREE_JSON):
        with open(TREE_JSON, encoding='utf-8') as f:
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
                # get children id(s)
                if 'childrenIds' in node_data:
                    children_ids = ','.join(node_data['childrenIds'])
                else:
                    # we have to find the children ids from the tree_json
                    children_ids = []
                    for child in tree_json['nodes']:
                        if 'parentIds' in tree_json['nodes'][child]:
                            if node in tree_json['nodes'][child]['parentIds']:
                                children_ids.append(child)
                    children_ids = ','.join(children_ids)
                # insert the node into the database
                c.execute("INSERT INTO nodes (id, parent_ids, children_ids, text, author, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                            (node, parent_ids, children_ids, node_data['text'], "Morpheus", timestamp))
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
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    data = request.get_json()
    print(data)
    # get parent id(s)
    if 'parentIds' in data:
        parent_ids = ','.join(data['parentIds'])
    else:
        parent_ids = data['parentId']
    # get children id(s)
    if 'childrenIds' in data:
        children_ids = ','.join(data['childrenIds'])
    else:
        children_ids = ''
    text = data['text']
    author = data['author']
    timestamp = data['timestamp']
    if 'id' in data:
        node_id = data['id']
    else:
        # generate a new id for the node
        node_id = uuid.uuid4().hex
    c.execute("INSERT INTO nodes (id, parent_ids, children_ids, text, author, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (node_id, parent_ids, children_ids, text, author, timestamp))
    # Add the operation to the history table
    c.execute("INSERT INTO history (timestamp, id, operation, author) VALUES (?, ?, ?, ?)",
                (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), node_id, 'create', author))
    db.commit()
    return jsonify({'success': True})

# Define a route for saving a set of new nodes to the database
@app.route('/nodes/batch', methods=['POST'])
def save_nodes():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    data = request.get_json()
    for node in data:
        # get parent id(s)
        if 'parentIds' in node:
            parent_ids = ','.join(node['parentIds'])
        else:
            parent_ids = node['parentId']
        # get children id(s)
        if 'childrenIds' in node:
            children_ids = ','.join(node['childrenIds'])
        else:
            children_ids = ''
        text = node['text']
        author = node['author']
        timestamp = node['timestamp']
        if 'id' in node:
            node_id = node['id']
        else:
            # generate a new id for the node
            node_id = uuid.uuid4().hex
        c.execute("INSERT INTO nodes (id, parent_ids, children_ids, text, author, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (node_id, parent_ids, children_ids, text, author, timestamp))
        # Add the operation to the history table
        c.execute("INSERT INTO history (id, timestamp, operation, author) VALUES (?, ?, ?, ?)",
                    (node_id, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), 'create', author))
    db.commit()
    return jsonify({'success': True})

# Define a route for updating an existing node in the database
@app.route('/nodes/<node_id>', methods=['PUT'])
def update_node(node_id):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    data = request.get_json()
    text = data['text']
    author = data['author']
    timestamp = data['timestamp']
    c.execute("UPDATE nodes SET text = ?, author = ?, timestamp = ? WHERE id = ?",
              (text, author, timestamp, node_id))
    # Add the operation to the history table
    c.execute("INSERT INTO history (timestamp, id, operation, author) VALUES (?, ?, ?, ?)",
                (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), node_id, 'update', author))
    db.commit()
    return jsonify({'success': True})

# Define a route for deleting a node from the database
@app.route('/nodes/<node_id>', methods=['DELETE'])
def delete_node(node_id):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    # Add the operation to the history table
    author = request.args.get('author')
    c.execute("INSERT INTO history (timestamp, id, operation, author) VALUES (?, ?, ?, ?)",
                (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), node_id, 'delete', author))
    db.commit()
    return jsonify({'success': True})

# Define a route for checking if a node exists in the database
@app.route('/nodes/exists/<node_id>', methods=['GET'])
def node_exists(node_id):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
    node = c.fetchone()
    if node:
        return jsonify({'success': True, 'exists': True})
    else:
        return jsonify({'success': True, 'exists': False})
    
# Define a route for checking if a list of nodes exists in the database
@app.route('/nodes/exists', methods=['POST'])
def nodes_exist():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    data = request.get_json()
    node_ids = data['nodeIds']
    exists = {}
    for node_id in node_ids:
        c.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        node = c.fetchone()
        if node:
            exists[node_id] = True
        else:
            exists[node_id] = False
    return jsonify({'success': True, 'exists': exists})

# Define a route for getting all nodes from the database after a given timestamp
@app.route('/nodes/get/<timestamp>', methods=['GET'])
def get_nodes(timestamp):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes WHERE timestamp > ?", (timestamp.replace("%"," "),))
    nodes = c.fetchall()
    # jsonify the nodes
    nodes = [{
        'id': node[0],
        'parent_ids': node[1].split(',') if node[1] else None,
        'children_ids': node[2].split(',') if node[2] else None,
        'text': node[3],
        'author': node[4],
        'timestamp': node[5]
    } for node in nodes]
    return jsonify({'success': True, 'nodes': nodes})

# Define a route for getting all node ids from the database
@app.route('/nodes/ids', methods=['GET'])
def get_all_node_ids():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT id FROM nodes")
    nodes = c.fetchall()
    # jsonify the nodes
    nodes = [node[0] for node in nodes]
    return jsonify({'success': True, 'nodes': nodes})

# Define a route for getting all nodes from the database
@app.route('/nodes', methods=['GET'])
def get_all_nodes():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes")
    nodes = c.fetchall()
    # jsonify the nodes
    nodes = {node[0]:{
        'parent_ids': node[1].split(',') if node[1] else None,
        'children_ids': node[2].split(',') if node[2] else None,
        'text': node[3],
        'author': node[4],
        'timestamp': node[5]
    } for node in nodes}
    return jsonify({'success': True, 'nodes': nodes})

# Define a route for getting the number of nodes in the database
@app.route('/nodes/count', methods=['GET'])
def get_node_count():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT COUNT(*) FROM nodes")
    count = c.fetchone()[0]
    return jsonify({'success': True, 'count': count})

# Define a route for getting a single node from the database
@app.route('/nodes/<node_id>', methods=['GET'])
def get_node(node_id):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
    node = c.fetchone()
    # jsonify the node
    node = {
        'id': node[0],
        'parent_ids': node[1].split(',') if node[1] else None,
        'children_ids': node[2].split(',') if node[2] else None,
        'text': node[3],
        'author': node[4],
        'timestamp': node[5]
    }
    return jsonify({'success': True, 'node': node})

# Define a route for getting the root node from the database
@app.route('/nodes/root', methods=['GET'])
def get_root_node():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes WHERE parent_ids IS NULL")
    node = c.fetchone()
    # jsonify the node
    node = {
        'id': node[0],
        'parent_ids': node[1].split(',') if node[1] else None,
        'children_ids': node[2].split(',') if node[2] else None,
        'text': node[3],
        'author': node[4],
        'timestamp': node[5]
    }
    return jsonify({'success': True, 'node': node})

# Define a route for getting the children of a node from the database
@app.route('/nodes/<node_id>/children', methods=['GET'])
def get_children(node_id):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes WHERE parent_ids LIKE ?", ('%'+node_id+'%',))
    nodes = c.fetchall()
    # jsonify the nodes
    nodes = [{
        'id': node[0],
        'parent_ids': node[1].split(',') if node[1] else None,
        'children_ids': node[2].split(',') if node[2] else None,
        'text': node[3],
        'author': node[4],
        'timestamp': node[5]
    } for node in nodes]
    return jsonify({'success': True, 'nodes': nodes})

# Define a route for getting the parents of a node from the database
@app.route('/nodes/<node_id>/parents', methods=['GET'])
def get_parents(node_id):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT * FROM nodes WHERE children_ids LIKE ?", ('%'+node_id+'%',))
    nodes = c.fetchall()
    # jsonify the nodes
    nodes = [{
        'id': node[0],
        'parent_ids': node[1].split(',') if node[1] else None,
        'children_ids': node[2].split(',') if node[2] else None,
        'text': node[3],
        'author': node[4],
        'timestamp': node[5]
    } for node in nodes]
    return jsonify({'success': True, 'nodes': nodes})

# Define a route for getting the history from the database
@app.route('/history', methods=['GET'])
def get_history():
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT * FROM history")
    history = c.fetchall()
    # jsonify the history
    history = [{
        'node_id': h[0],
        'timestamp': h[1],
        'operation': h[2],
        'author': h[3]
    } for h in history]
    return jsonify({'success': True, 'history': history})

# Define a route for getting the history from the database after a certain timestamp
@app.route('/history/<timestamp>', methods=['GET'])
def get_history_after(timestamp):
    # Check if the user is authorized to make changes to the database
    if not is_authorized(request.headers.get('Authorization')):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    # Check if the tree id is correct
    if request.headers.get('Tree-Id') != TREE_ID:
        return jsonify({'success': False, 'error': 'Invalid Tree-Id'})
    db, c = get_db()
    c.execute("SELECT * FROM history WHERE timestamp > ?", (timestamp,))
    history = c.fetchall()
    # jsonify the history
    history = [{
        'node_id': h[0],
        'timestamp': h[1],
        'operation': h[2],
        'author': h[3]
    } for h in history]
    return jsonify({'success': True, 'history': history})

app.run(host="0.0.0.0", port=SERVER_PORT, debug=True)