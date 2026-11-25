import sqlite3

def run_migration():
    conn = sqlite3.connect("retinasahayak.db")
    cursor = conn.cursor()

    def get_columns(table):
        cursor.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]

    ref_cols = get_columns("referrals")
    required_ref_cols = [
        ("patient_anonymized_id", "VARCHAR(64)"),
        ("phc_location", "VARCHAR(128)"),
        ("health_worker_id", "VARCHAR(36)"),
        ("assigned_ophthalmologist_id", "VARCHAR(36)"),
        ("predicted_grade", "INTEGER"),
        ("confidence", "FLOAT"),
        ("uncertainty_status", "VARCHAR(32)"),
        ("referable_status", "VARCHAR(32)"),
        ("priority", "VARCHAR(32) DEFAULT 'MEDIUM'"),
        ("referral_reason", "TEXT"),
        ("escalation_reason", "VARCHAR(64)"),
        ("escalation_notes", "TEXT"),
        ("closed_by", "VARCHAR(36)"),
        ("close_reason", "VARCHAR(64)"),
        ("close_notes", "TEXT"),
        ("created_at", "DATETIME"),
        ("updated_at", "DATETIME"),
        ("closed_at", "DATETIME")
    ]

    for col_name, col_type in required_ref_cols:
        if col_name not in ref_cols:
            print(f"Adding {col_name} to referrals")
            cursor.execute(f"ALTER TABLE referrals ADD COLUMN {col_name} {col_type}")

    cr_cols = get_columns("clinical_reviews")
    required_cr_cols = [
        ("ai_predicted_grade", "INTEGER"),
        ("ai_confidence", "FLOAT"),
        ("final_grade", "INTEGER"),
        ("clinical_decision", "VARCHAR(64)"),
        ("agrees_with_ai", "BOOLEAN DEFAULT 1"),
        ("review_status", "VARCHAR(32) DEFAULT 'COMPLETED'")
    ]

    for col_name, col_type in required_cr_cols:
        if col_name not in cr_cols:
            print(f"Adding {col_name} to clinical_reviews")
            cursor.execute(f"ALTER TABLE clinical_reviews ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print("Migration finished successfully.")

if __name__ == "__main__":
    run_migration()
