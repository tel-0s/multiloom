import unittest
import json
import requests

class TestServer(unittest.TestCase):

    def setUp(self):
        self.url = 'http://localhost:5000'

    def test_save_node(self):
        # Test saving a new node to the database
        data = {
            'parent_id': "",
            'text': 'Test node',
            'author': 'Test author',
            'timestamp': '2022-01-01 00:00:00'
        }
        response = requests.post(f'{self.url}/nodes', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})

    def test_update_node(self):
        # Test updating an existing node in the database
        data = {
            'text': 'Updated node',
            'author': 'Updated author',
            'timestamp': '2022-01-01 00:00:00'
        }
        response = requests.put(f'{self.url}/nodes/1', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})

if __name__ == '__main__':
    unittest.main()