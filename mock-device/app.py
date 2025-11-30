from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/config")
def config():
    return {
        "running_config": "hostname MOCK-DEVICE\ninterface Gi0/1\n ip address 10.10.10.1 255.255.255.0"
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
