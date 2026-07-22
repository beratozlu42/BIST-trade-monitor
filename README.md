# BIST Trade Monitor

A Python application that monitors real-time BIST trade data from a Telegram Mini App and sends Telegram notifications when unusual trading activity is detected.

## Features

- Real-time trade monitoring
- Large trade detection
- Block trade detection
- Telegram notifications
- Monitors multiple stocks simultaneously
- Dynamic lot threshold based on recent trading history

---

## Requirements

- Python 3.10 or newer
- Google Chrome or Chromium

---

## Installation

Clone or download this project.

Install the required packages:

```bash
pip install -r requirements.txt
```

Install the Playwright browser:

```bash
playwright install chromium
```

---

## Configuration

Open `app.py` and configure the following variables:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
```

You can create a Telegram bot using **@BotFather**.

---

## First Run

Start the program:

```bash
python app.py
```

The first time:

1. Telegram Web will open.
2. Log in with your Telegram account.
3. Open **@ucretsizderinlikbot**.
4. Launch the Mini App.
5. Press **Enter** in the terminal.

The login session will be saved automatically. You won't need to log in again.

---

## Stopping the Program

Press:

```text
CTRL + C
```

The bot will send a notification indicating that the monitoring system has stopped.

---

## Notes

- Keep the browser window open while monitoring.
- Do not manually close Chromium while the program is running.
- The Telegram Mini App session expires after approximately 30 minutes and must be reopened.