# جدولة التحديث الدوري
def schedule_flush(interval_seconds=30):
    def run():
        while True:
            time.sleep(interval_seconds)
            flush_to_db()
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()


    
    # بدء جدولة التحديث كل 30 ثانية
    schedule_flush(interval_seconds=30)

