"""Temporary diagnostic test script for date resolution.

This script tests various date input formats to observe parsing behavior.
Run this and observe the console output to understand date parsing.
"""

from app.agent.orchestrator import Orchestrator
from app.memory.repo import MemoryRepo
from app.db.session import SessionLocal

# Test date inputs
test_inputs = [
    "Summarize my meeting with MTCA on December 12th, 2025",
    "Summarize my meeting with MTCA on December 12th",
    "Summarize my meeting with MTCA on Dec 12",
    "Summarize my meeting with MTCA on 12/12/2025",
]

def run_diagnostic():
    """Run diagnostic tests."""
    print("\n" + "=" * 80)
    print("DIAGNOSTIC TEST SCRIPT")
    print("=" * 80)
    print("\nThis script will test various date input formats.")
    print("Observe the console output to understand date parsing behavior.\n")
    
    db = SessionLocal()
    try:
        memory_repo = MemoryRepo(db)
        orchestrator = Orchestrator(memory_repo)
        
        for test_input in test_inputs:
            print("\n" + "=" * 80)
            print(f"TESTING: {test_input}")
            print("=" * 80)
            
            try:
                result = orchestrator.process_message(test_input)
                print(f"\nRESULT: {result.get('message', '')[:200]}...")
            except Exception as e:
                print(f"\nERROR: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "-" * 80)
    finally:
        db.close()

if __name__ == "__main__":
    run_diagnostic()

