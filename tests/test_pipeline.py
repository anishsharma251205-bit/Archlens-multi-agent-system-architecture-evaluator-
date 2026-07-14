import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import evaluate

test_input = """
A simple e-commerce app with a React frontend, a single Node.js backend server,
and one PostgreSQL database. All deployed on a single EC2 instance.
"""

result = evaluate(test_input)

print("\n--- FINAL RESULT ---")
print(f"Final Score: {result.final_score}/10")
print(f"\nReport:\n{result.final_report}")