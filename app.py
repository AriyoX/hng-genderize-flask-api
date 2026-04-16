from flask import Flask, jsonify, request
from datetime import datetime, timezone
import requests

app = Flask(__name__)

GENDERIZE_URL = "https://api.genderize.io"


def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


app.after_request(add_cors_headers)


@app.route("/api/classify", methods=["GET"])
def classify_name():
    name = request.args.get("name")

    if name is None or name == "":
        return jsonify({"status": "error", "message": "Missing or empty name parameter"}), 400

    if not isinstance(name, str):
        return jsonify({"status": "error", "message": "name must be a string"}), 422

    try:
        resp = requests.get(GENDERIZE_URL, params={"name": name}, timeout=4)
        resp.raise_for_status()
        payload = resp.json()
    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "message": "Upstream API timed out"}), 502
    except requests.exceptions.RequestException as exc:
        return jsonify({"status": "error", "message": f"Upstream API error: {str(exc)}"}), 502

    gender = payload.get("gender")
    count = payload.get("count", 0)
    probability = payload.get("probability", 0)

    if gender is None or count == 0:
        return jsonify({"status": "error", "message": "No prediction available for the provided name"}), 200

    sample_size = count
    is_confident = probability >= 0.7 and sample_size >= 100
    processed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return jsonify({
        "status": "success",
        "data": {
            "name": payload.get("name", name).lower(),
            "gender": gender,
            "probability": probability,
            "sample_size": sample_size,
            "is_confident": is_confident,
            "processed_at": processed_at,
        }
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
