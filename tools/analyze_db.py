"""
Database Analysis Script - Check available data by vehicle class
"""

import pyodbc

# Database connection (Load from environment variables)
import os

DB_SERVER = os.getenv('MSSQL_SERVER')
DB_PORT = os.getenv('MSSQL_PORT', '1433')
DB_NAME = os.getenv('MSSQL_DATABASE')
DB_USER = os.getenv('MSSQL_USERNAME')
DB_PASS = os.getenv('MSSQL_PASSWORD')

# Validate required environment variables
if not all([DB_SERVER, DB_NAME, DB_USER, DB_PASS]):
    raise ValueError("Missing required database credentials. Set: MSSQL_SERVER, MSSQL_DATABASE, MSSQL_USERNAME, MSSQL_PASSWORD")

# Class mapping
CCH_TO_CLASS = {
    1: 'TWO_WHEELER', 2: 'THREE_WHEELER', 3: 'THREE_WHEELER',
    4: 'CAR', 5: 'LCV', 6: 'LCV', 7: 'BUS', 8: 'BUS', 9: 'BUS',
    10: 'TRUCK', 11: 'TRUCK', 12: 'TRUCK', 13: 'TRUCK', 14: 'TRUCK', 15: 'TRUCK',
    16: 'HEAVY_MACHINERY', 17: 'HEAVY_MACHINERY', 18: 'TRACTOR', 19: 'TRACTOR', 20: 'LCV'
}

def main():
    print("=" * 70)
    print("DATABASE ANALYSIS - Vehicle Class Distribution")
    print("=" * 70)
    
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={DB_SERVER},{DB_PORT};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASS};"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=30;"
    )
    
    print("\nConnecting to database...")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print("Connected!")
    
    # Check date range
    print("\n" + "-" * 70)
    print("DATE RANGE:")
    
    cursor.execute("""
        SELECT 
            MIN(TXN_COMBINE_TIME) as first_date,
            MAX(TXN_COMBINE_TIME) as last_date,
            COUNT(*) as total_count
        FROM [HTMS_EPE].[dbo].[TBL_COMBINED_TRANSACTION]
        WHERE LEN(EN_ANPR_IMAGE_PATH) > 5 AND LEN(EX_ANPR_IMAGE_PATH) > 5
    """)
    row = cursor.fetchone()
    print(f"  First transaction: {row[0]}")
    print(f"  Last transaction:  {row[1]}")
    print(f"  Total transactions: {row[2]}")
    
    # Count by CCH class
    print("\n" + "-" * 70)
    print("VEHICLE CLASS DISTRIBUTION (by CCH_CLASS):")
    print("-" * 70)
    print(f"{'CCH':<6} {'Class Name':<35} {'Count':>10}")
    print("-" * 70)
    
    cursor.execute("""
        SELECT 
            c.EN_TAG_CCH_CLASS,
            m.CCH_CLASS_TEXT,
            COUNT(*) as cnt
        FROM [HTMS_EPE].[dbo].[TBL_COMBINED_TRANSACTION] c
        LEFT JOIN [HTMS_EPE].[dbo].[TBL_CCH_CLASS_MASTER] m 
            ON c.EN_TAG_CCH_CLASS = m.CCH_CLASS
        WHERE LEN(c.EN_ANPR_IMAGE_PATH) > 5 AND LEN(c.EX_ANPR_IMAGE_PATH) > 5
        AND c.EN_TAG_CCH_CLASS IS NOT NULL
        GROUP BY c.EN_TAG_CCH_CLASS, m.CCH_CLASS_TEXT
        ORDER BY c.EN_TAG_CCH_CLASS
    """)
    
    total = 0
    grouped = {}
    
    for row in cursor:
        cch = row[0] if row[0] else 0
        text = row[1] if row[1] else 'Unknown'
        cnt = row[2]
        print(f"{cch:<6} {text:<35} {cnt:>10}")
        total += cnt
        
        # Group by simplified class
        class_name = CCH_TO_CLASS.get(cch, 'OTHER')
        grouped[class_name] = grouped.get(class_name, 0) + cnt
    
    print("-" * 70)
    print(f"{'TOTAL':<41} {total:>10}")
    
    # Show grouped counts
    print("\n" + "-" * 70)
    print("GROUPED BY VEHICLE TYPE:")
    print("-" * 70)
    print(f"{'Class':<20} {'Count':>10} {'Images (x2)':>15}")
    print("-" * 70)
    
    for cls in ['CAR', 'LCV', 'TRUCK', 'BUS', 'TWO_WHEELER', 'THREE_WHEELER', 'TRACTOR', 'HEAVY_MACHINERY']:
        cnt = grouped.get(cls, 0)
        images = cnt * 2  # Each pair = 2 images
        print(f"{cls:<20} {cnt:>10} {images:>15}")
    
    print("-" * 70)
    print(f"{'TOTAL':<20} {sum(grouped.values()):>10} {sum(grouped.values())*2:>15}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION:")
    print("=" * 70)
    print("For ReID training, you need ~1000-2000 samples per class.")
    print("Each sample = 2 images (ENTRY + EXIT)")
    print()
    print("Next step: Run 'python prepare_reid_classwise.py' to create dataset")
    print("=" * 70)

if __name__ == "__main__":
    main()
