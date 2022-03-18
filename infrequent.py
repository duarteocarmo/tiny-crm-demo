import pathlib
from dateutil.relativedelta import relativedelta
import datetime
import boto3
from botocore.exceptions import ClientError
import sys


def parse_interval(text):
    text = text.lower().strip()
    assert len(text.split(" ")) == 2
    value, units = text.split(" ")
    value = int(value)

    if "month" in units:
        return relativedelta(months=value)
    elif "year" in units:
        return relativedelta(years=value)
    elif "week" in units:
        return relativedelta(weeks=value)

    else:
        return None


def get_list_of_updates():
    people_folder = "people"
    today = datetime.datetime.today()
    to_contact = list()

    for file in pathlib.Path(people_folder).glob("**/*.md"):

        lines = file.read_text().splitlines()

        name = lines[0].removeprefix("Name:").strip()
        relation = lines[1].removeprefix("Relationship:").strip()

        contact_frequency = lines[2].removeprefix("Interval(every):").strip().lower()
        time_delta = parse_interval(contact_frequency)

        interaction_dates_str = [
            _.removeprefix("##").strip() for _ in lines if _.startswith("## ")
        ]
        interaction_dates = [
            datetime.datetime.strptime(_, "%d-%m-%Y")
            for _ in interaction_dates_str
            if _
        ]
        interaction_dates.sort()
        last_interaction_date = interaction_dates[-1]

        next_interaction_date = last_interaction_date + time_delta

        delay = today - last_interaction_date
        delay_in_days = delay.days
        message = f"{name} - {relation} - (Cadency: every {contact_frequency}, {delay_in_days} days passed since last contact)"

        if next_interaction_date < today:
            to_contact.append(message)

        print(last_interaction_date)
        print(message)
        print("==" * 89)

    return to_contact


def send_email_to_myself(subject, body_text, body_html):
    CHARSET = "UTF-8"
    SENDER = "Duarte O.Carmo <duarteocarmo@gmail.com>"
    RECIPIENT = "duarteocarmo@gmail.com"
    AWS_REGION = "eu-west-1"
    client = boto3.client("ses", region_name=AWS_REGION)

    try:
        client.send_email(
            Destination={
                "ToAddresses": [
                    RECIPIENT,
                ],
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": CHARSET,
                        "Data": body_html,
                    },
                    "Text": {
                        "Charset": CHARSET,
                        "Data": body_text,
                    },
                },
                "Subject": {
                    "Charset": CHARSET,
                    "Data": subject,
                },
            },
            Source=SENDER,
        )
    except ClientError as e:
        print(e.response["Error"]["Message"])
        return False
    else:
        print("Email was sent :)")
        return True


list_of_updates = get_list_of_updates()

if not list_of_updates:
    print("No updates missing, exiting")
    sys.exit()


subject = f"🎙 You need to reach out to {len(list_of_updates)} people"
body_text = "You need to reach out to\n"
body_html = """<html>
<head></head>
<body>
  <p>Hi Duarte, please reach out to:</p>
  <ul>
  """

if list_of_updates:
    print("Updates to send:")
    for update in list_of_updates:
        print(update)
        body_text += update + "\n"
        body_html += f"<li>{update}</li>"
else:
    update = "Nobody to update :)"
    body_text += update + "\n"
    body_html += f"<li>{update}</li>"

body_html += """
</ul>
</body>
</html>
"""

send_email_to_myself(subject=subject, body_html=body_html, body_text=body_text)
