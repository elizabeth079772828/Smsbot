BTN_TEMPLATE = "template"
BTN_DEVICES = "devices"
BTN_NUMBERS = "numbers"
BTN_CODES = "codes"
BTN_LINK = "link"
BTN_SEND = "send"
BTN_STATUS = "status"
BTN_BACK = "back"


def main_menu():
    return {
        "inline_keyboard": [
            [{"text": "📝 Message Template", "callback_data": BTN_TEMPLATE}],
            [{"text": "🔥 Firebase Devices", "callback_data": BTN_DEVICES}],
            [{"text": "📱 Upload Numbers", "callback_data": BTN_NUMBERS}],
            [{"text": "🔢 Upload Codes", "callback_data": BTN_CODES}],
            [{"text": "🔗 Set Link", "callback_data": BTN_LINK}],
            [{"text": "📊 Status", "callback_data": BTN_STATUS}],
            [{"text": "🚀 Send Now", "callback_data": BTN_SEND}],
        ]
    }


def back_menu():
    return {"inline_keyboard": [[{"text": "⬅️ Back", "callback_data": BTN_BACK}]]}