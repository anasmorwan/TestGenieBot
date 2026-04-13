from storage.sqlite_db import flush_to_db
from apscheduler.schedulers.background import BackgroundScheduler
from services/backup_service.py import backup_all

scheduler = BackgroundScheduler()

# جدولة التحديث الدوري
def schedule_flush(interval_seconds=30):
    def run():
        while True:
            time.sleep(interval_seconds)
            flush_to_db()
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()







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
    
    
