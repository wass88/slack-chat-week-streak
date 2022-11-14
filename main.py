import os
from slack_sdk import WebClient
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=+9), 'JST')
start_of_day = 6
def now():
    #return datetime.now(JST).replace(day=31) + timedelta(days=1)
    return datetime.now(JST)
def last_week():
    return (now() - timedelta(days=7)).replace(microsecond=0,second=0,minute=0,hour=start_of_day)
def last_month():
    return (now() - timedelta(days=1)).replace(microsecond=0,second=0,minute=0,hour=start_of_day,day=1)
def today():
    return now().replace(microsecond=0,second=0,minute=0,hour=start_of_day)
def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(float(timestamp), JST)

class Slack:
    def __init__(self):
        self.client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
    def send(self, channel, text):
        self.client.chat_postMessage(channel=channel, text=text)
    def read(self, channel, oldest):
        cursor = ""
        messages = []
        for _ in range(10):
            resp = self.client.conversations_history(channel=channel, limit=100, oldest=oldest.timestamp(), cursor=cursor)
            by_user = [msg for msg in resp.data["messages"] if msg.get("bot_id") is None and msg.get("subtype") is None]
            for msg in by_user:
                msg["username"] = self.user(msg["user"])
            messages.extend(by_user)
            cursor = resp.data.get("response_metadata", {}).get("next_cursor")
            if cursor is None:
                break
        return messages
    def user(self, user_id):
        if not hasattr(self, "usernames"):
            self.usernames = {}
        if self.usernames.get(user_id) is None: 
            resp = self.client.users_info(user=user_id)
            self.usernames[user_id] = resp.data["user"]["name"]
        return self.usernames[user_id]

def message_streak(messages, oldest, latest):
    print(oldest, latest)
    days = (latest - oldest).days
    post_users_days = {}
    for msg in messages:
        day = timestamp_to_date(msg["ts"])
        day_index = (day - oldest).days
        if day_index < 0 or day_index >= days:
            continue
        if post_users_days.get(msg["username"]) is None:
            post_users_days[msg["username"]] = [0 for _ in range(days)]
        post_users_days[msg["username"]][day_index] += 1
    return post_users_days

def streak_to_msg(streak):
    if not streak:
        return "投稿なし"
    msg = ""
    user_len = max(len(user) for user in streak.keys())
    for user, days in streak.items():
        str = "".join(("O" if day > 0 else ".") for day in days)
        usr = user.ljust(user_len)
        msg += f"{usr} : {str}\n"
    return f"```\n{msg}```"

slack = Slack()
channel = os.environ['CHANNEL']
def tests():
    #slack.send(channel, "Hello world!")
    #print([m for m in slack.read(channel, last_week())])
    def ts_before(hours):
        return str((now() - timedelta(hours=hours)).timestamp())
    test_msgs = [
        {"username": "user1", "ts": ts_before(32)},
        {"username": "user1", "ts": ts_before(2)},
        {"username": "user1", "ts": ts_before(129)},
        {"username": "user20", "ts": ts_before(81)},
        {"username": "user20", "ts": ts_before(999)},
    ]
    test_streak = {'user1': [0, 0, 1, 0, 0, 0, 1], 'user20': [0, 0, 0, 0, 1, 0, 0]}
    print(message_streak(test_msgs, last_week(), today()))
    print(streak_to_msg(test_streak))

def main():
    if now().weekday() == 0:
        week_post()
    if now().day == 1:
        month_post()

def week_post():
    messages = slack.read(channel, last_week())
    streak = message_streak(messages, last_week(), today())
    msg = streak_to_msg(streak)
    print(msg)
    slack.send(channel, "先週のトレーニング\n"+msg)

def month_post():
    messages = slack.read(channel, last_month())
    streak = message_streak(messages, last_month(), today())
    msg = streak_to_msg(streak)
    print(msg)
    slack.send(channel, "先月のトレーニング\n"+msg)

import base64
def slack_training_streak(event, context):
    print("""This Function was triggered by messageId {} published at {} to {}
    """.format(context.event_id, context.timestamp, context.resource["name"]))

    if 'data' in event:
        name = base64.b64decode(event['data']).decode('utf-8')
    else:
        name = 'World'
    print('Hello {}!'.format(name))

    main()

if __name__ == "__main__":
    main()