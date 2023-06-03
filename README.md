# Multiloom

Multiloom is a multi-user variation of the tree-based GPT-powered writing interface [Loom](https://github.com/socketeer/loom) with a focus on collaborative writing. It is currently in early development and is not yet ready for use.

## Features

* Collaborative editing: Multiple users can edit the same tree simultaneously, with changes synced in real time and attributed to users. Changes are replayed when users join.
* Read mode: Includes a linear story view, tree nav bar, and edit mode.
* Tree view: Allows users to explore the tree visually with the mouse, expand and collapse nodes, change tree topology, and edit nodes in place.
* Navigation: Includes hotkeys, bookmarks, chapters, and a 'visited' state.
* Generation: Allows users to generate N children with GPT-3, modify generation settings, and change hidden memory on a node-by-node basis.
* File I/O: Allows users to open/save trees as JSON files, work with trees in multiple tabs, and combine trees.

## Server

The server-side code for Multiloom is contained in the `server.py` file. It defines several routes for handling HTTP requests, including creating, updating, and deleting nodes in a database, as well as retrieving all nodes after a given timestamp.

To use the server, you'll need to have a database set up and running. You'll also need to modify the `is_authorized` function to check for valid authorization credentials.

Once you have those set up, you can run the server by running the `server.py` file. The server will listen for incoming HTTP requests on the specified port.

## Routes

The following routes are defined in the `server.py` file:

- `POST /nodes`: Create a new node in the database.
- `PUT /nodes/<node_id>`: Update an existing node in the database.
- `DELETE /nodes/<node_id>`: Delete a node from the database.
- `GET /nodes/get/<timestamp>`: Retrieve all nodes from the database after a given timestamp.

## Dependencies

This file requires the following dependencies:

- `flask`: A Python web framework for handling HTTP requests.

Please note that Multiloom is currently in early development and is not yet ready for use.