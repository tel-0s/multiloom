# A simple client for multiloom

import requests
import json
import tkinter as tk
from tkinter import ttk
import time

class Client(tk.Tk):
    def __init__(self, url, headers):
        super().__init__()
        self.url = url
        self.headers = headers
        self.title('Multiloom Client')
        self.geometry('600x400')
        self.resizable(True, True)
        self.create_widgets()
        self.get_nodes()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=('text', 'author', 'timestamp'))
        self.tree.heading('#0', text='ID')
        self.tree.heading('text', text='Text')
        self.tree.heading('author', text='Author')
        self.tree.heading('timestamp', text='Timestamp')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(self, height=5)
        self.text.pack(fill=tk.BOTH, expand=True)

        self.author = tk.Entry(self)
        self.author.pack(fill=tk.BOTH, expand=True)

        self.save_button = tk.Button(self, text='Save', command=self.save_node)
        self.save_button.pack(fill=tk.BOTH, expand=True)

        self.update_button = tk.Button(self, text='Update', command=self.update_node)
        self.update_button.pack(fill=tk.BOTH, expand=True)

        self.tree.bind('<<TreeviewSelect>>', self.select_node)

    # On selecting a node in the tree, populate the text field with the node's text
    def select_node(self, event):
        if len(self.tree.selection()) > 0:
            item = self.tree.selection()[0]
            self.text.delete('1.0', tk.END)
            self.text.insert('1.0', self.tree.item(item)['values'][0])

    def get_nodes(self, timestamp='2021-01-01 00:00:00'):
        response = requests.get(f'{self.url}/nodes/get/{timestamp}', headers=self.headers)
        if response.status_code == 200:
            self.tree.delete(*self.tree.get_children())
            for node in response.json()['nodes']:
                self.tree.insert('', 'end', text=node['id'], values=(node['text'], node['author'], node['timestamp']))

    def save_node(self):
        data = {
            'parent_id': "",
            'text': self.text.get('1.0', tk.END),
            'author': self.author.get(),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        response = requests.post(f'{self.url}/nodes', json=data, headers=self.headers)
        if response.status_code == 200:
            self.get_nodes()

    def update_node(self):
        if len(self.tree.selection()) == 0:
            return

        data = {
            'text': self.text.get('1.0', tk.END),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        # define node url
        item = self.tree.selection()[0]
        node_id = self.tree.item(item)['text']
        # if the node has a different author & the new one isn't included, add it
        if self.author.get().lower() not in self.tree.item(item)['values'][1].lower():
            data['author'] = f'{self.tree.item(item)["values"][1]}, {self.author.get()}'
        else:
            data['author'] = self.tree.item(item)['values'][1]
        response = requests.put(f'{self.url}/nodes/{node_id}', json=data, headers=self.headers)

        if response.status_code == 200:
            self.get_nodes()

if __name__ == '__main__':
    cli = Client("http://localhost:8080", {"Authorization":"123456"})
    cli.mainloop()