from storage.sqlite_db import flush_to_db

# جدولة التحديث الدوري
def schedule_flush(interval_seconds=30):
    def run():
        while True:
            time.sleep(interval_seconds)
            flush_to_db()
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()


    
    
