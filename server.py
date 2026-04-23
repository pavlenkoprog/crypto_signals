"""
server.py — веб-сервер с историей сигналов.
Запуск: python server.py
"""
from flask import Flask, jsonify, send_from_directory
import os
from core.signal_logger import read_signals
from core.trade_logger import read_trades

app = Flask(__name__, static_folder=os.path.dirname(__file__))


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/signals")
def api_signals():
    return jsonify(read_signals(200))


@app.route("/api/trades")
def api_trades():
    return jsonify(read_trades(200))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
