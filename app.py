# app.py
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
import sys
import boto3
from datetime import datetime, timedelta, time
from threading import Thread
from collections import defaultdict
from dateutil import parser
from boto3.dynamodb.conditions import Key, Attr
from zoneinfo import ZoneInfo  # Python 3.9+

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# AWS DynamoDB setup
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"]
)

table_name = os.environ["DYNAMODB_TABLE_NAME"]
table = dynamodb.Table(table_name)

IST = ZoneInfo("Asia/Kolkata")  # Set Indian timezone


def write_to_dynamodb(user_id, username, status):
    try:
        item = {
            "user_id": user_id,
            "username": username,
            "status": status,
            "timestamp": datetime.now(IST).isoformat()
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
        Thread(target=write_to_dynamodb, args=(user_id, username, final_status)).start()

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


@app.route("/api/attendance", methods=["GET"])
def get_attendance():
    try:
        response = table.scan()
        items = response["Items"]

        # Sort by timestamp
        items.sort(key=lambda x: x["timestamp"])

        latest_per_user_per_day = {}
        for item in items:
            dt = parser.isoparse(item["timestamp"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=ZoneInfo("UTC"))
            local_dt = dt.astimezone(IST)
            date_str = local_dt.date().isoformat()

            key = (item["user_id"], date_str)
            latest_per_user_per_day[key] = {
                "user_id": item["user_id"],
                "username": item.get("username", "unknown"),
                "status": item["status"]
            }

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
        user_id = request.form.get("user_id")
        username = request.form.get("username")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")

        if not user_id or not username or not start_date_str or not end_date_str:
            return render_template("applyleave.html", message="❌ All fields are required.")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date < start_date:
                return render_template("applyleave.html", message="❌ End date cannot be before start date.")

            current_date = start_date
            while current_date <= end_date:
                dt = datetime.combine(current_date, time(0, 0)).replace(tzinfo=IST)
                item = {
                    "user_id": user_id,
                    "username": username,
                    "status": "On Leave",
                    "timestamp": dt.isoformat()
                }
                table.put_item(Item=item)
                current_date += timedelta(days=1)

            return render_template("applyleave.html", message="✅ Leave successfully recorded.")

        except Exception as e:
            print("Leave application error:", str(e))
            return render_template("applyleave.html", message="❌ Something went wrong.")

    return render_template("applyleave.html")


@app.route("/cancelleave", methods=["GET", "POST"])
def cancel_leave():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        username = request.form.get("username")
        start_date_str = request.form.get("start_date")
        end_date_str = request.form.get("end_date")

        if not user_id or not username or not start_date_str or not end_date_str:
            return render_template("cancelleave.html", message="❌ All fields are required.")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            if end_date < start_date:
                return render_template("cancelleave.html", message="❌ End date cannot be before start date.")

            deleted_dates = []
            current_date = start_date
            while current_date <= end_date:
                timestamp_prefix = f"{current_date.isoformat()}T"

                response = table.scan(
                    FilterExpression=Attr("user_id").eq(user_id) & Attr("timestamp").begins_with(timestamp_prefix)
                )

                for item in response.get("Items", []):
                    if item.get("status") == "On Leave":
                        table.delete_item(
                            Key={"user_id": item["user_id"], "timestamp": item["timestamp"]}
                        )
                        deleted_dates.append(current_date.isoformat())

                current_date += timedelta(days=1)

            if deleted_dates:
                return render_template("cancelleave.html", message=f"✅ Leave cancelled for: {', '.join(deleted_dates)}")
            else:
                return render_template("cancelleave.html", message="⚠️ No leave found to cancel in this range.")

        except Exception as e:
            print("Cancel leave error:", str(e))
            return render_template("cancelleave.html", message="❌ Something went wrong.")

    return render_template("cancelleave.html")


@app.route("/")
def homepage():
    return render_template("home.html")


if __name__ == "__main__":
    app.run(debug=True)
