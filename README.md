# Telegram-Automation-VPN-Sell-Bot-


Telegram Auto-Poster Bot
This is a powerful Telegram Bot built with aiogram 3.x designed for channel administrators. It allows you to queue posts (photos, videos, albums, polls, and text), manage them via an admin panel, and automatically schedule them to be posted to your channels.

Features
Media Queue Management: Upload photos, videos, albums, and polls directly to the bot to queue them.

Admin Panel: View, navigate, and delete queued posts from a user-friendly inline menu.

Scheduling: Set specific times (cron-style) for automatic posts or use an interval-based schedule.

Customization: Add a dynamic watermark or signature to your posts automatically.

Smart Database: Uses SQLite to store post data and settings, ensuring nothing is lost after a restart.

Delete After Post: Optional setting to automatically remove posts from the database once they are published.

Technologies Used
Language: Python 3.10+

Framework: aiogram (Asynchronous Telegram Bot API)

Scheduling: APScheduler

Database: SQLite3

How to Setup
1. Prerequisites
Ensure you have Python installed, then install the required dependencies:

Bash
pip install aiogram apscheduler pytz
2. Configuration
Open your main script and update the CONFIG section:

TOKEN: Your bot token from BotFather.

ADMIN_ID: Your Telegram User ID.

CHANNEL_IDS: A list of channel usernames or IDs where the bot should post.

3. Run the Bot
Bash
python main.py
How to Use
Start the Bot: Send /start to your bot.

Upload Content: Simply send photos, videos, or polls to the bot. It will automatically save them to the queue.

Admin Panel: * View Queue: Review all saved posts.

Settings: Change the posting schedule (e.g., 08:00, 19:40) or set a custom watermark.

Post Now: Manually trigger the posting process.

Database Structure
The bot uses bot_db.py (ensure this file exists in your project folder) to manage:

posts: Stores file IDs, captions, and posting status.

settings: Stores bot configurations like schedule and watermark.

Contributing
Feel free to fork this project and add new features like support for more media types or advanced analytics.
