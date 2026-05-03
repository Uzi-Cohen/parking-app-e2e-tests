# slot_service.py

import requests
from notification_service import notification_queue

def calculate_parking_fee(duration):
    # חישוב פשוט לדוגמה, תעדכן לפי הצורך
    rate_per_hour = 10  # ש"ח לשעה
    hours = max(1, int(duration // 60))  # מעגלים לשעה
    return rate_per_hour * hours

def free_slot(slot_id, license_plate, duration):
    # 1. שחרור החניה במערכת (הלוגיקה הקיימת שלך)
    # למשל:
    # update_slot_status(slot_id, 'free')

    # 2. חיוב דרך שירות Billing (REST API)
    amount = calculate_parking_fee(duration)
    try:
        res = requests.post(
            "http://localhost:5002/charge",
            json={
                "license_plate": license_plate,
                "amount": amount
            },
            timeout=5
        )
        billing_status = res.json().get("status", "error")
    except Exception as e:
        billing_status = "error"
        print("שגיאה בשירות החיוב:", e)

    # 3. שליחת התראה אסינכרונית
    message = f"חניה {slot_id} שוחררה לרכב {license_plate} (סטטוס חיוב: {billing_status})"
    notification_queue.put((slot_id, message))

    # 4. להחזיר סטטוס (לא חובה)
    return {"slot_id": slot_id, "license_plate": license_plate, "billing_status": billing_status}
