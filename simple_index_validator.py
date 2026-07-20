#!/usr/bin/env python3
"""
SIMPLIFIED INDEX PERFORMANCE VALIDATOR

Tests EXPLAIN ANALYZE output before and after index creation
"""

import psycopg2
import time
import json

DB_CONFIG = {
    'host': 'localhost', 'port': 5432, 'database': 'vayuguard',
    'user': 'postgres', 'password': ''
}

FORECAST_QUERY = """
SELECT lag_1, lag_3, lag_6, lag_12, lag_24,
       rolling_mean_6, rolling_mean_12, rolling_mean_24,
       rolling_std_6, rolling_std_12, rolling_std_24,
       hour, day_of_week, month, quarter, day_of_month
FROM engineered_features
WHERE city = %s
ORDER BY date DESC
LIMIT 1
"""

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def run_explain_analyze(label, city='Chennai'):
    """Run EXPLAIN ANALYZE and extract metrics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"\n[⏱️ ] {label}...")
    
    try:
        # Run EXPLAIN ANALYZE with JSON output
        explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {FORECAST_QUERY}"
        cursor.execute(explain_sql, (city,))
        
        # Fetch and parse result
        result = cursor.fetchone()[0]
        
        # Result is a list with plan and metrics
        if isinstance(result, str):
            data = json.loads(result)
        else:
            data = result
        
        # Extract timing and plan info
        plan_info = data[0]  # The query plan
        timing_info = data[1]  # Timing/summary info
        
        execution_time = timing_info['Execution Time']
        planning_time = timing_info['Planning Time']
        
        # Analyze the plan
        plan = plan_info['Plan']
        node_type = plan.get('Node Type', 'Unknown')
        index_name = plan.get('Index Name', None)
        
        print(f"    Planning: {planning_time:.2f}ms")
        print(f"    Execution: {execution_time:.2f}ms")
        print(f"    Plan Node: {node_type}")
        if index_name:
            print(f"    Index Used: {index_name}")
        else:
            print(f"    Index Used: NONE (sequential scan)")
        
        cursor.close()
        conn.close()
        
        return {
            'planning_time': planning_time,
            'execution_time': execution_time,
            'node_type': node_type,
            'index_used': index_name
        }
    
    except Exception as e:
        print(f"    ❌ Error: {e}")
        cursor.close()
        conn.close()
        return None

def create_index():
    """Create the performance index"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"\n[🔧] Creating index...")
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_engineered_features_city_date 
            ON engineered_features(city, date DESC)
        """)
        conn.commit()
        print(f"    ✓ Index created")
        
        cursor.execute("ANALYZE engineered_features")
        conn.commit()
        print(f"    ✓ ANALYZE completed")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"    ❌ Error: {e}")
        cursor.close()
        conn.close()
        return False

def drop_index():
    """Drop the index for fresh test"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DROP INDEX IF EXISTS idx_engineered_features_city_date")
        conn.commit()
        print(f"[✓] Dropped existing index (fresh start)")
        cursor.close()
        conn.close()
        return True
    except:
        cursor.close()
        conn.close()
        return True

def main():
    print("\n" + "="*80)
    print("INDEX PERFORMANCE VALIDATION")
    print("="*80)
    
    # Check table
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM engineered_features")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print(f"\n[📊] Table: engineered_features ({count:,} rows)")
    
    # Drop index for clean test
    drop_index()
    
    # Test WITHOUT index
    before = run_explain_analyze("STEP 1: Test WITHOUT index")
    if not before:
        return 1
    
    # Create index
    if not create_index():
        return 1
    
    # Test WITH index
    after = run_explain_analyze("STEP 2: Test WITH index")
    if not after:
        return 1
    
    # Compare
    print(f"\n" + "="*80)
    print("RESULTS")
    print(f"="*80)
    
    before_time = before['execution_time']
    after_time = after['execution_time']
    improvement = ((before_time - after_time) / before_time) * 100
    speedup = before_time / after_time if after_time > 0 else float('inf')
    
    print(f"\n[⏱️ ] EXECUTION TIME:")
    print(f"    Before: {before_time:>8.2f}ms")
    print(f"    After:  {after_time:>8.2f}ms")
    print(f"    Saving: {(before_time - after_time):>8.2f}ms per query")
    print(f"    Improvement: {improvement:>6.1f}% ({speedup:.1f}x faster)")
    
    print(f"\n[🔍] PLAN ANALYSIS:")
    print(f"    Before: {before['node_type']} - Index: {before['index_used'] or 'NONE'}")
    print(f"    After:  {after['node_type']} - Index: {after['index_used'] or 'NONE'}")
    
    # Diagnosis
    print(f"\n" + "="*80)
    if improvement > 80:
        print(f"✅ ROOT CAUSE CONFIRMED")
        print(f"\nThe missing index is the PRIMARY bottleneck (saves {improvement:.0f}%).")
        print(f"DECISION: Deploy index to production immediately.")
    elif improvement > 50:
        print(f"⚠️ SIGNIFICANT IMPROVEMENT")
        print(f"\nThe index helps ({improvement:.0f}% improvement), but investigate remaining:")
        print(f"- Connection pooling limits")
        print(f"- Other slow queries")
        print(f"- Database resource constraints")
    else:
        print(f"❌ MINOR IMPROVEMENT")
        print(f"\nThe index has limited impact ({improvement:.0f}% improvement).")
        print(f"Continue investigating other bottlenecks.")
    print(f"="*80 + "\n")
    
    return 0

if __name__ == '__main__':
    exit(main())
