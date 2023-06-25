import unittest
import json
import requests

class TestServer(unittest.TestCase):

    def setUp(self):
        self.url = 'http://localhost:8080'
        self.headers = {
            "Authorization":"123456"
        }

    def test_save_node(self):
        # Test saving a new node to the database
        data = {
            'parentId': "",
            'text': 'Test node',
            'author': 'Test author',
            'timestamp': '2022-01-01 00:00:00'
        }
        response = requests.post(f'{self.url}/nodes', json=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})

    def test_update_node(self):
        # Test updating an existing node in the database
        data = {
            'text': 'Updated node',
            'author': 'Updated author',
            'timestamp': '2022-01-01 00:00:00'
        }
        response = requests.put(f'{self.url}/nodes/1', json=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})

    def test_get_nodes(self):
        # Test getting all nodes from the database after a given timestamp
        response = requests.get(f'{self.url}/nodes/get/2021-01-01 00:00:00', headers=self.headers)
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

    def test_get_node_ids(self):
        # Test getting all node ids from the database
        response = requests.get(f'{self.url}/nodes/ids', headers=self.headers)
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

    def test_node_exists(self):
        # Test checking if a node exists in the database
        response = requests.get(f'{self.url}/nodes/exists/1', headers=self.headers)
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

    def test_get_history(self):
        # Test getting the history from the database
        response = requests.get(f'{self.url}/history', headers=self.headers)
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

if __name__ == '__main__':
    unittest.main()