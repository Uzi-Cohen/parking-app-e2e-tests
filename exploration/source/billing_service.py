# billing_service.py
from flask import Flask, request, jsonify

app = Flask(__name__)
charges = []

@app.route("/charge", methods=["POST"])
def charge():
    data = request.json
    license_plate = data["license_plate"]
    amount = data["amount"]
    charges.append({"license_plate": license_plate, "amount": amount})
    print(f"חוייב רכב {license_plate} בסך {amount} ש\"ח")
    return jsonify({"status": "paid"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002, debug=False)
