from flask import Flask, render_template, request
from flask_cors import CORS

from config import port, global_dir

import json

import os

app = Flask(__name__, template_folder = os.path.join(global_dir, "static"))
CORS(app)

@app.route('/')
def index():
    return render_template('client.html')


light = 'black'
leftPointerDeg = -30
leftPointer2Deg = 30
rightPointerDeg = 90
rdata =  600
speedDashboard =  list([])
msg = list(['msg1', 'msg2', 'msg3'])

global data

@app.route('/refresh', methods=['POST'])
def refresh():
    cmdList = request.form.get('cmdList')
    data = {
        'light': light,
        'leftPointerDeg': leftPointerDeg,
        'leftPointer2Deg': leftPointer2Deg,
        'rightPointerDeg': rightPointerDeg,
        'rdata': rdata,
        'speedDashboard': speedDashboard,
        'msg': list(msg)
    }
    data['msg'].append(cmdList)
    return json.dumps(json.loads(json.dumps(data, ensure_ascii=False)))

if __name__ == '__main__':
    app.run(debug=True, port = port)