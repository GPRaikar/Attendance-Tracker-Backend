# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from boto3.dynamodb.conditions import Key
import dateutil.parser
import json
import os
import sys
import boto3
from datetime import datetime
from threading import Thread
from collections import defaultdict  # <-- make sure this import is present
from dateutil import parser         # <-- also ensure this is imported

app = Flask(__name__, static_folder='static', template_folder='templates')

CORS(app)  # Allow cross-origin requests from frontend

# Set up DynamoDB client using environment variables
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"]
)

table_name = os.environ["DYNAMODB_TABLE_NAME"]
table = dynamodb.Table(table_name)

def write_to_dynamodb(user_id, username, status):
    try:
        item = {
            "user_id": user_id,
            "username": username,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        table.put_item(Item=item)
        print(f"[{user_id}] saved: {status}")
        sys.stdout.flush()
    except Exception as e:
        print(f"[{user_id}] failed to save to DynamoDB:", e)
        sys.stdout.flush()

@app.route("/slack/interact", methods=["POST"])
def handle_interaction():
    try:
        payload = json.loads(request.form["payload"])
        print("Payload received:", json.dumps(payload, indent=2))
        sys.stdout.flush()

        user_id = payload["user"]["id"]
        username = payload["user"].get("username", "unknown")
        action_id = payload["actions"][0]["action_id"]

        status_map = {
            "wfh": "Work from Home",
            "leave": "On Leave",
            "wfo": "Work from Office"
        }

        if action_id not in status_map:
            return jsonify({"text": "❌ Unknown action."}), 200

        final_status = status_map[action_id]

        # Start background thread to write to DynamoDB
        Thread(target=write_to_dynamodb, args=(user_id, username, final_status)).start()

        print(f"[{user_id}] selected: {final_status}")
        sys.stdout.flush()

        # Send confirmation immediately
        return jsonify({
            "replace_original": True,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ Your attendance has been recorded as *{final_status}*."
                    }
                }
            ]
        })

    except Exception as e:
        print("Error handling interaction:", str(e))
        sys.stdout.flush()
        return jsonify({"text": f"⚠️ Internal error: {str(e)}"}), 200



# @app.route("/api/attendance", methods=["GET"])
# def get_attendance():
#     try:
#         response = table.scan()
#         items = response["Items"]

#         # Normalize timestamp to date
#         attendance_by_date = {}
#         for item in items:
#             date_str = dateutil.parser.parse(item["timestamp"]).date().isoformat()
#             if date_str not in attendance_by_date:
#                 attendance_by_date[date_str] = []
#             attendance_by_date[date_str].append({
#                 "user_id": item["user_id"],
#                 "username": item.get("username", "unknown"),
#                 "status": item["status"]
#             })

#         return jsonify(attendance_by_date)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@app.route("/api/attendance", methods=["GET"])
def get_attendance():
    try:
        response = table.scan()
        items = response["Items"]

        # Sort items by timestamp (oldest to newest)
        items.sort(key=lambda x: x["timestamp"])

        # Keep only the latest record per (user_id, date)
        latest_per_user_per_day = {}
        for item in items:
            date_str = parser.parse(item["timestamp"]).date().isoformat()
            key = (item["user_id"], date_str)
            latest_per_user_per_day[key] = {
                "user_id": item["user_id"],
                "username": item.get("username", "unknown"),
                "status": item["status"]
            }

        # Group by date
        attendance_by_date = defaultdict(list)
        for (user_id, date_str), record in latest_per_user_per_day.items():
            attendance_by_date[date_str].append(record)

        return jsonify(dict(attendance_by_date))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/calendar")
def calendar_view():
    return render_template("calendar.html")



@app.route("/applyleave", methods=["GET", "POST"])
def apply_leave():
    if request.method == "POST":
        data = request.json
        username = data.get("username")
        date_str = data.get("date")

        if not username or not date_str:
            return jsonify({"error": "Missing fields"}), 400

        # Store with dummy user_id since it's a manual entry
        item = {
            "user_id": f"manual-{username}",
            "username": username,
            "status": "On Leave",
            "timestamp": f"{date_str}T00:00:00Z"
        }

        table.put_item(Item=item)
        return jsonify({"success": True}), 200

    return render_template("apply_leave.html")

@app.route("/")
def homepage():
    return render_template("home.html")
