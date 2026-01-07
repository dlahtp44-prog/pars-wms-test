def upsert_inventory(
    warehouse: str,
    location: str,
    brand: str,
    item_code: str,
    item_name: str,
    lot: str,
    spec: str,
    qty_delta: int,
    note: str = "",
) -> None:
    """
    ✅ 재고 upsert 정책
    - 동일 key(warehouse/location/brand/item_code/lot/spec) 존재 시:
        * qty, note, updated_at 만 변경
        * ❌ item_name 변경 금지
    - 신규 row 생성 시에만 item_name 저장
    """
    now = datetime.now().isoformat(timespec="seconds")

    # normalize
    warehouse = (warehouse or "").strip()
    location = (location or "").strip()
    brand = (brand or "").strip()
    item_code = (item_code or "").strip()
    item_name = (item_name or "").strip()
    lot = (lot or "").strip()
    spec = (spec or "").strip()
    note = (note or "").strip()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, qty
        FROM inventory
        WHERE warehouse=? AND location=? AND brand=?
          AND item_code=? AND lot=? AND spec=?
    """, (warehouse, location, brand, item_code, lot, spec))

    row = cur.fetchone()

    if row:
        # 🔒 기존 재고: 품명 유지
        new_qty = max(0, int(row["qty"]) + int(qty_delta))
        cur.execute("""
            UPDATE inventory
            SET qty=?, note=?, updated_at=?
            WHERE id=?
        """, (
            new_qty,
            note,
            now,
            int(row["id"]),
        ))
    else:
        # 🆕 신규 재고만 품명 저장
        cur.execute("""
            INSERT INTO inventory
            (warehouse, location, brand, item_code, item_name,
             lot, spec, qty, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            warehouse,
            location,
            brand,
            item_code,
            item_name,
            lot,
            spec,
            max(0, int(qty_delta)),
            note,
            now,
        ))

    conn.commit()
    conn.close()
