from flask import Flask, request, jsonify
import json
import sys

app = Flask(__name__)

@app.route("/slack/interact", methods=["POST"])
def handle_interaction():
    try:
        payload = json.loads(request.form["payload"])
        print("Payload received:", json.dumps(payload, indent=2))
        sys.stdout.flush()

        user_id = payload["user"]["id"]
        action_id = payload["actions"][0]["action_id"]

        if action_id == "wfo":
            print(f"[{user_id}] selected: Work from Office - asking for sub-location")
            sys.stdout.flush()
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
            final_status = status_map[action_id]
            print(f"[{user_id}] selected: {final_status}")
            sys.stdout.flush()

            return jsonify({
                "replace_original": True,
                "text": f"✅ Your attendance has been recorded as *{final_status}*."
            })

        return jsonify({"text": "Unknown action."}), 200

    except Exception as e:
        print("Error handling interaction:", str(e))
        sys.stdout.flush()
        return jsonify({"text": f"⚠️ Internal error: {str(e)}"}), 200
