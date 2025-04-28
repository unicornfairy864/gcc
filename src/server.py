from flask import Flask, render_template, request

from config import port, global_dir

import os

app = Flask(__name__, template_folder = os.path.join(global_dir, "templates"))

@app.route('/')
def index():
    return render_template('client.html', port = port)

@app.route('/refresh', methods=['POST'])
def refresh():
    return request.form.get("cmdList")

if __name__ == '__main__':
    app.run(debug=True, port = port)