from flask import Flask, request, jsonify
import sqlite3
import threading
import uuid

app = Flask(__name__)

# Create the nodes table
conn = sqlite3.connect('tree.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS nodes
             (id TEXT PRIMARY KEY,
              parent_id TEXT,
              text TEXT,
              author TEXT,
              timestamp TEXT)''')
conn.commit()
conn.close()

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
    db, c = get_db()
    data = request.get_json()
    parent_id = data['parent_id']
    text = data['text']
    author = data['author']
    timestamp = data['timestamp']
    # generate a new id for the node
    node_id = uuid.uuid4().hex
    c.execute("INSERT INTO nodes (id, parent_id, text, author, timestamp) VALUES (?, ?, ?, ?, ?)",
                (node_id, parent_id, text, author, timestamp))
    db.commit()
    return jsonify({'success': True})

# Define a route for updating an existing node in the database
@app.route('/nodes/<int:node_id>', methods=['PUT'])
def update_node(node_id):
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
@app.route('/nodes/<int:node_id>', methods=['DELETE'])
def delete_node(node_id):
    db, c = get_db()
    c.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    db.commit()
    return jsonify({'success': True})

app.run()