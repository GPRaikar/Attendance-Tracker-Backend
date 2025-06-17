# app.py
from flask import Flask, request, jsonify
import json
import os
import sys
import boto3
from datetime import datetime

app = Flask(__name__)

# Set up DynamoDB client using environment variables
dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_REGION"]
)

table_name = os.environ["DYNAMODB_TABLE_NAME"]
table = dynamodb.Table(table_name)

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

        # Save to DynamoDB
        item = {
            "user_id": user_id,
            "username": username,
            "status": final_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        table.put_item(Item=item)

        print(f"[{user_id}] selected: {final_status}")
        sys.stdout.flush()

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



# from flask import Flask, request, jsonify
# import json
# import os
# import sys
# import boto3
# from datetime import datetime

# app = Flask(__name__)

# # Setup DynamoDB
# dynamodb = boto3.resource(
#     "dynamodb",
#     aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
#     aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
#     region_name=os.environ["AWS_REGION"]
# )
# table = dynamodb.Table(os.environ["DYNAMODB_TABLE_NAME"])

# @app.route("/slack/interact", methods=["POST"])
# def handle_interaction():
#     try:
#         payload = json.loads(request.form["payload"])
#         print("Payload received:", json.dumps(payload, indent=2))
#         sys.stdout.flush()

#         user_id = payload["user"]["id"]
#         username = payload["user"].get("username", "unknown")
#         action_id = payload["actions"][0]["action_id"]

#         if action_id == "wfo":
#             print(f"[{user_id}] selected: Work from Office - asking for sub-location")
#             sys.stdout.flush()
#             return jsonify({
#                 "replace_original": True,
#                 "blocks": [
#                     {
#                         "type": "section",
#                         "text": {"type": "mrkdwn", "text": "*Which office location?*"}
#                     },
#                     {
#                         "type": "actions",
#                         "block_id": "sub_location",
#                         "elements": [
#                             {
#                                 "type": "button",
#                                 "text": {"type": "plain_text", "text": "Main Office"},
#                                 "value": "main",
#                                 "action_id": "wfo_main"
#                             },
#                             {
#                                 "type": "button",
#                                 "text": {"type": "plain_text", "text": "Satellite Office"},
#                                 "value": "satellite",
#                                 "action_id": "wfo_satellite"
#                             }
#                         ]
#                     }
#                 ]
#             })

#         elif action_id in ["wfh", "leave", "wfo_main", "wfo_satellite"]:
#             status_map = {
#                 "wfh": "Work from Home",
#                 "leave": "On Leave",
#                 "wfo_main": "Work from Office (Main)",
#                 "wfo_satellite": "Work from Office (Satellite)"
#             }
#             final_status = status_map[action_id]

#             item = {
#                 "user_id": user_id,
#                 "username": username,
#                 "status": final_status,
#                 "timestamp": datetime.utcnow().isoformat(),
#                 "date": datetime.utcnow().strftime("%Y-%m-%d")
#             }
#             table.put_item(Item=item)

#             print(f"[{user_id}] recorded: {final_status}")
#             sys.stdout.flush()

#             return jsonify({
#                 "replace_original": True,
#                 "blocks": [
#                     {
#                         "type": "section",
#                         "text": {
#                             "type": "mrkdwn",
#                             "text": f"✅ Your attendance has been recorded as *{final_status}*."
#                         }
#                     }
#                 ]
#             })

#         return jsonify({"text": "Unknown action."}), 200

#     except Exception as e:
#         print("Error handling interaction:", str(e))
#         sys.stdout.flush()
#         return jsonify({"text": f"⚠️ Internal error: {str(e)}"}), 200
