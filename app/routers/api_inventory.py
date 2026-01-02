@router.get("/qr")
def inventory_by_qr(code: str):
    code = code.strip()  # 🔥 줄바꿈 제거

    conn = get_db()
    cur = conn.cursor()

    # 1️⃣ 로케이션 QR 조회
    cur.execute("""
        SELECT warehouse, location, item_code, item_name, lot, size, quantity
        FROM inventory
        WHERE location = ?
        ORDER BY item_code, lot, size
    """, (code,))
    rows = cur.fetchall()

    if rows:
        return [
            {
                "warehouse": r[0],
                "location": r[1],
                "item_code": r[2],
                "item_name": r[3],
                "lot": r[4],
                "spec": r[5],
                "qty": r[6],
            }
            for r in rows
        ]

    # 2️⃣ 제품 QR (item|lot|spec)
    try:
        item_code, lot, spec = code.split("|")
    except:
        return []

    cur.execute("""
        SELECT warehouse, location, item_code, item_name, lot, size, quantity
        FROM inventory
        WHERE item_code=? AND lot=? AND size=?
    """, (item_code, lot, spec))

    rows = cur.fetchall()
    return [
        {
            "warehouse": r[0],
            "location": r[1],
            "item_code": r[2],
            "item_name": r[3],
            "lot": r[4],
            "spec": r[5],
            "qty": r[6],
        }
        for r in rows
    ]
