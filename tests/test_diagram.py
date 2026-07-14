import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_client import describe_diagram
from agents.orchestrator import evaluate

with open("data/your_diagram.jpg", "rb") as f:
    image_bytes = f.read()

description = describe_diagram(image_bytes, "image/jpeg")
print("--- DESCRIPTION ---")
print(description)

result = evaluate(description)

print("\n--- SCORES ---")
print(f"Structure:   {result.structure.score}/10")
print(f"Security:    {result.security.score}/10")
print(f"Scalability: {result.scalability.score}/10")
print(f"Performance: {result.performance.score}/10")
print(f"Cost:        {result.cost.score}/10")
print(f"\nFinal: {result.final_score}/10")