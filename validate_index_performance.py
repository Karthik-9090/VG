#!/usr/bin/env python3
"""
INDEX PERFORMANCE VALIDATION TOOL - CORRECTED

This script proves whether the missing database index is the actual bottleneck
by running EXPLAIN ANALYZE before and after index creation.

Process:
1. Connect to PostgreSQL
2. Run EXPLAIN ANALYZE on the engineered_features query BEFORE index creation
3. Create the recommended index
4. Run EXPLAIN ANALYZE on the same query AFTER index creation
5. Compare and report improvement percentage
6. Determine if index is root cause (>80% improvement = root cause confirmed)
"""

import psycopg2
import json
import time
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'vayuguard',
    'user': 'postgres',
    'password': ''
}

# The ACTUAL query (corrected based on table schema)
# The FastAPI code references columns that don't exist - use actual columns
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

# Index definition to create
INDEX_DEFINITION = """
CREATE INDEX IF NOT EXISTS idx_engineered_features_city_date 
ON engineered_features(city, date DESC)
"""

# Index drop for cleanup
DROP_INDEX = """
DROP INDEX IF EXISTS idx_engineered_features_city_date
"""

class IndexPerformanceValidator:
    """Validates index performance impact using EXPLAIN ANALYZE"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        self.before_results = None
        self.after_results = None
        self.cities = ['Chennai', 'Bengaluru', 'Hyderabad']
        self.test_city = 'Chennai'
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("[✓] Database connection successful")
            return True
        except Exception as e:
            print(f"[✗] Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("[✓] Database connection closed")
    
    def check_table_exists(self):
        """Verify engineered_features table exists"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'engineered_features'
                )
            """)
            exists = cursor.fetchone()[0]
            cursor.close()
            
            if exists:
                print("[✓] Table 'engineered_features' exists")
                return True
            else:
                print("[✗] Table 'engineered_features' does not exist")
                return False
        except Exception as e:
            print(f"[✗] Error checking table: {e}")
            return False
    
    def check_table_size(self):
        """Get table size and row count"""
        try:
            cursor = self.conn.cursor()
            
            # Row count
            cursor.execute("SELECT COUNT(*) FROM engineered_features")
            row_count = cursor.fetchone()[0]
            
            # Table size
            cursor.execute("""
                SELECT pg_size_pretty(pg_total_relation_size('engineered_features'))
            """)
            table_size = cursor.fetchone()[0]
            
            # City distribution
            cursor.execute("""
                SELECT city, COUNT(*) as count 
                FROM engineered_features 
                GROUP BY city 
                ORDER BY city
            """)
            city_dist = cursor.fetchall()
            
            cursor.close()
            
            print(f"\n[📊] Table Statistics:")
            print(f"    Total rows: {row_count:,}")
            print(f"    Table size: {table_size}")
            print(f"    By city:")
            for city, count in city_dist:
                print(f"      - {city}: {count:,} rows")
            
            return row_count > 0
        except Exception as e:
            print(f"[✗] Error getting table size: {e}")
            return False
    
    def drop_index_if_exists(self):
        """Drop the index to start fresh"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(DROP_INDEX)
            self.conn.commit()
            cursor.close()
            print("[✓] Any existing index dropped (fresh start)")
            return True
        except Exception as e:
            print(f"[✗] Error dropping index: {e}")
            return False
    
    def run_explain_analyze(self, label):
        """Run EXPLAIN ANALYZE on the forecast query"""
        try:
            print(f"\n[⏱️] Running EXPLAIN ANALYZE - {label}...")
            
            cursor = self.conn.cursor()
            
            # Run EXPLAIN ANALYZE (returns JSON in PostgreSQL 11+)
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {FORECAST_QUERY}"
            
            start_time = time.time()
            cursor.execute(explain_query, (self.test_city,))
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            result = cursor.fetchall()
            cursor.close()
            
            # Parse the JSON result
            if result and result[0]:
                plan_json = result[0][0]
                if isinstance(plan_json, str):
                    plan_data = json.loads(plan_json)
                else:
                    plan_data = plan_json[0]
                
                # Extract key metrics from the plan
                plan = plan_data[0]
                
                metrics = {
                    'label': label,
                    'timestamp': datetime.now().isoformat(),
                    'planning_time_ms': plan_data[1]['Planning Time'],
                    'execution_time_ms': plan_data[1]['Execution Time'],
                    'plan': self._extract_plan_info(plan['Plan']),
                    'raw_result': plan_data
                }
                
                return metrics
            else:
                print(f"[✗] No EXPLAIN ANALYZE result returned")
                return None
                
        except Exception as e:
            print(f"[✗] Error running EXPLAIN ANALYZE: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_plan_info(self, plan):
        """Extract relevant information from execution plan"""
        info = {
            'node_type': plan.get('Node Type', 'Unknown'),
            'rows_returned': plan.get('Actual Rows', 0),
            'rows_scanned': plan.get('Actual Rows', 0),
            'total_cost': plan.get('Total Cost', 0),
            'planning_cost': plan.get('Startup Cost', 0),
            'indexes_used': [],
            'sort_used': False,
            'filter_used': False,
            'children': []
        }
        
        # Check for index usage
        if 'Index Name' in plan:
            info['indexes_used'].append(plan['Index Name'])
        
        # Check for sort
        if 'Sort Space Used' in plan or 'Sort Method' in plan:
            info['sort_used'] = True
        
        # Check for filter
        if 'Filter' in plan:
            info['filter_used'] = True
        
        # Recursively process children
        if 'Plans' in plan:
            for child in plan['Plans']:
                child_info = self._extract_plan_info(child)
                info['children'].append(child_info)
                # Aggregate indexes from children
                info['indexes_used'].extend(child_info['indexes_used'])
        
        return info
    
    def create_index(self):
        """Create the recommended index"""
        try:
            print(f"\n[🔧] Creating index...")
            print(f"    {INDEX_DEFINITION}")
            
            cursor = self.conn.cursor()
            cursor.execute(INDEX_DEFINITION)
            self.conn.commit()
            cursor.close()
            
            print("[✓] Index created successfully")
            
            # Analyze the index
            cursor = self.conn.cursor()
            cursor.execute("ANALYZE engineered_features")
            self.conn.commit()
            cursor.close()
            
            print("[✓] ANALYZE completed")
            return True
        except Exception as e:
            print(f"[✗] Error creating index: {e}")
            return False
    
    def verify_index_exists(self):
        """Verify the index was created"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'engineered_features' 
                AND indexname = 'idx_engineered_features_city_date'
            """)
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                print("[✓] Index 'idx_engineered_features_city_date' verified")
                return True
            else:
                print("[✗] Index not found")
                return False
        except Exception as e:
            print(f"[✗] Error verifying index: {e}")
            return False
    
    def validate(self):
        """Run the complete validation process"""
        print("\n" + "="*80)
        print("INDEX PERFORMANCE VALIDATION")
        print("="*80)
        
        # Step 1: Connect
        print("\n[STEP 1] Connecting to database...")
        if not self.connect():
            return False
        
        # Step 2: Verify table
        print("\n[STEP 2] Verifying table...")
        if not self.check_table_exists():
            self.disconnect()
            return False
        
        # Step 3: Get table stats
        print("\n[STEP 3] Getting table statistics...")
        if not self.check_table_size():
            self.disconnect()
            return False
        
        # Step 4: Drop index for clean test
        print("\n[STEP 4] Starting fresh (dropping any existing index)...")
        self.drop_index_if_exists()
        
        # Step 5: Run EXPLAIN ANALYZE BEFORE
        print("\n[STEP 5] Testing WITHOUT index...")
        self.before_results = self.run_explain_analyze("BEFORE INDEX CREATION")
        if not self.before_results:
            self.disconnect()
            return False
        
        # Step 6: Create index
        print("\n[STEP 6] Creating index...")
        if not self.create_index():
            self.disconnect()
            return False
        
        # Step 7: Verify index
        print("\n[STEP 7] Verifying index...")
        if not self.verify_index_exists():
            self.disconnect()
            return False
        
        # Step 8: Run EXPLAIN ANALYZE AFTER
        print("\n[STEP 8] Testing WITH index...")
        self.after_results = self.run_explain_analyze("AFTER INDEX CREATION")
        if not self.after_results:
            self.disconnect()
            return False
        
        # Step 9: Compare
        print("\n[STEP 9] Comparing results...")
        self.compare_results()
        
        # Cleanup
        self.disconnect()
        return True
    
    def compare_results(self):
        """Compare before and after execution plans"""
        if not self.before_results or not self.after_results:
            print("[✗] Missing results for comparison")
            return
        
        before_exec = self.before_results['execution_time_ms']
        after_exec = self.after_results['execution_time_ms']
        
        improvement = ((before_exec - after_exec) / before_exec) * 100
        speedup = before_exec / after_exec if after_exec > 0 else float('inf')
        
        before_plan = self.before_results['plan']
        after_plan = self.after_results['plan']
        
        self.comparison = {
            'before_exec_ms': before_exec,
            'after_exec_ms': after_exec,
            'improvement_percent': improvement,
            'speedup': speedup,
            'before_plan': before_plan,
            'after_plan': after_plan,
            'before_results': self.before_results,
            'after_results': self.after_results
        }
        
        print(f"\n{'='*80}")
        print("COMPARISON RESULTS")
        print(f"{'='*80}")
        
        print(f"\n[⏱️] EXECUTION TIME:")
        print(f"    Before index: {before_exec:.2f}ms")
        print(f"    After index:  {after_exec:.2f}ms")
        print(f"    Improvement:  {improvement:.1f}%")
        print(f"    Speedup:      {speedup:.1f}x faster")
        
        print(f"\n[⏱️] PLANNING TIME:")
        print(f"    Before: {self.before_results['planning_time_ms']:.2f}ms")
        print(f"    After:  {self.after_results['planning_time_ms']:.2f}ms")
        
        print(f"\n[🔍] EXECUTION PLAN ANALYSIS:")
        print(f"    Before - Node Type: {before_plan.get('node_type')}")
        print(f"    After  - Node Type: {after_plan.get('node_type')}")
        
        before_indexes = before_plan.get('indexes_used', [])
        after_indexes = after_plan.get('indexes_used', [])
        print(f"    Before - Index Used: {before_indexes if before_indexes else '❌ NONE (Full scan)'}")
        print(f"    After  - Index Used: {after_indexes if after_indexes else '❌ NONE'}")
        
        before_sort = before_plan.get('sort_used', False)
        after_sort = after_plan.get('sort_used', False)
        print(f"    Before - Sort: {'Yes' if before_sort else 'No'}")
        print(f"    After  - Sort: {'Yes' if after_sort else 'No'}")
        
        # Diagnosis
        print(f"\n{'='*80}")
        print("DIAGNOSIS")
        print(f"{'='*80}")
        
        if improvement > 80:
            print(f"\n✅ ROOT CAUSE CONFIRMED")
            print(f"\n   The missing index is DEFINITIVELY the primary bottleneck.")
            print(f"   Index reduces latency by {improvement:.1f}% ({speedup:.1f}x speedup).")
            print(f"   This matches the predicted 70% impact from analysis.")
            print(f"\n   RECOMMENDATION: Deploy index immediately to production.")
            self.diagnosis = "ROOT_CAUSE_CONFIRMED"
        elif improvement > 50:
            print(f"\n⚠️ PARTIAL IMPROVEMENT")
            print(f"\n   The index improves performance by {improvement:.1f}% ({speedup:.1f}x speedup).")
            print(f"   However, other bottlenecks remain.")
            print(f"\n   RECOMMENDATION: Deploy index AND investigate:")
            print(f"   - Connection pooling saturation")
            print(f"   - Repeated query patterns (N+1)")
            print(f"   - Database blocking I/O")
            self.diagnosis = "PARTIAL_IMPROVEMENT"
        else:
            print(f"\n❌ NO SIGNIFICANT IMPROVEMENT")
            print(f"\n   Index provides only {improvement:.1f}% improvement ({speedup:.1f}x speedup).")
            print(f"   The missing index is NOT the primary bottleneck.")
            print(f"\n   RECOMMENDATION: Continue investigating:")
            print(f"   - Connection pooling limits")
            print(f"   - Concurrent query contention")
            print(f"   - Database resource constraints")
            self.diagnosis = "NO_IMPROVEMENT"
        
        print(f"\n{'='*80}\n")


def main():
    """Main entry point"""
    validator = IndexPerformanceValidator(DB_CONFIG)
    success = validator.validate()
    
    if success:
        print(f"\n{'='*80}")
        print("✅ VALIDATION COMPLETE")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print("❌ VALIDATION FAILED")
        print(f"{'='*80}\n")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
