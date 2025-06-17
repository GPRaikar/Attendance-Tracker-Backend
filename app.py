from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route("/slack/interact", methods=["POST"])
def handle_interaction():
    payload = json.loads(request.form["payload"])
    user_id = payload["user"]["id"]
    action_id = payload["actions"][0]["action_id"]

    if action_id == "wfo":
        return jsonify({
            "replace_original": True,
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Which office location?*"}
                },
                {
                    "type": "actions",
                    "block_id": "sub_location",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Main Office"},
                            "value": "main",
                            "action_id": "wfo_main"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Satellite Office"},
                            "value": "satellite",
                            "action_id": "wfo_satellite"
                        }
                    ]
                }
            ]
        })

    elif action_id in ["wfh", "leave", "wfo_main", "wfo_satellite"]:
        status_map = {
            "wfh": "Work from Home",
            "leave": "On Leave",
            "wfo_main": "Work from Office (Main)",
            "wfo_satellite": "Work from Office (Satellite)"
        }
        return jsonify({
            "replace_original": True,
            "text": f"✅ Your attendance has been recorded as *{status_map[action_id]}*."
        })

    return "", 200

@app.route("/", methods=["GET"])
def home():
    return "Slack Attendance Bot Backend is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)





# from flask import Flask, request, jsonify
# import json

# app = Flask(__name__)

# @app.route("/slack/interact", methods=["POST"])
# def handle_interaction():
#     payload = json.loads(request.form["payload"])
#     user_id = payload["user"]["id"]
#     action_id = payload["actions"][0]["action_id"]

#     if action_id == "wfo":
#         return jsonify({
#             "replace_original": True,
#             "blocks": [
#                 {
#                     "type": "section",
#                     "text": {
#                         "type": "mrkdwn",
#                         "text": "*Which office location?*"
#                     }
#                 },
#                 {
#                     "type": "actions",
#                     "block_id": "sub_location",
#                     "elements": [
#                         {
#                             "type": "button",
#                             "text": {"type": "plain_text", "text": "Main Office"},
#                             "value": "main",
#                             "action_id": "wfo_main"
#                         },
#                         {
#                             "type": "button",
#                             "text": {"type": "plain_text", "text": "Satellite Office"},
#                             "value": "satellite",
#                             "action_id": "wfo_satellite"
#                         }
#                     ]
#                 }
#             ]
#         })

#     elif action_id in ["wfh", "leave", "wfo_main", "wfo_satellite"]:
#         status_map = {
#             "wfh": "Work from Home",
#             "leave": "On Leave",
#             "wfo_main": "Work from Office (Main)",
#             "wfo_satellite": "Work from Office (Satellite)"
#         }
#         return jsonify({
#             "replace_original": True,
#             "text": f"✅ Your attendance has been recorded as *{status_map[action_id]}*."
#         })

#     return "", 200

# if __name__ == "__main__":
#     app.run(port=3000)
