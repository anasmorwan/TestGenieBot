from storage.sqlite_db import flush_to_db
from apscheduler.schedulers.background import BackgroundScheduler
from services/backup_service.py import backup_all

scheduler = BackgroundScheduler()


def schedule_flush(interval_seconds=30):
    scheduler.add_job(
        func=flush_to_db,
        trigger='interval',
        seconds=interval_seconds,
        id='chat_collection',
        replace_existing=True
    )
    
def start_auto_backup():
    scheduler.add_job(
        func=backup_all,
        trigger='interval',
        minutes=30,
        id='auto_backup',
        replace_existing=True
        )

def start_daily_challenge():
    from bot.notifications.trap import send_daily_challenge_message  # استيراد محلي
    scheduler.add_job(
        send_daily_challenge_message,
        'interval',
        hours=1,
        id='daily_challenge',
        replace_existing=True
    )
    
    
