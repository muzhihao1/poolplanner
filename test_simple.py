#!/usr/bin/env python3
"""
简单的Flask测试应用
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <html>
        <head><title>测试页面</title></head>
        <body>
            <h1>Flask测试成功！</h1>
            <p>如果你能看到这个页面，说明Flask可以正常工作。</p>
            <p><a href="/api/test">测试API端点</a></p>
        </body>
    </html>
    '''

@app.route('/api/test')
def api_test():
    return {'status': 'ok', 'message': 'API工作正常'}

if __name__ == '__main__':
    print("启动测试服务器在 http://localhost:8888")
    app.run(debug=True, port=8888)