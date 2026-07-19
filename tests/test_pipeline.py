import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator import evaluate

test_input = """
A ride-sharing app with a React frontend served via CloudFront CDN,
Node.js API gateway with JWT authentication, separate microservices for
users, rides, and payments each with their own PostgreSQL database on RDS,
Redis for session caching, deployed on AWS ECS with autoscaling,
Stripe with PCI-DSS compliance, HTTPS on all endpoints, VPC with
security groups, CloudWatch monitoring.
"""


result = evaluate(test_input)

print("\n--- FINAL RESULT ---")
print(f"Final Score: {result.final_score}/10")
print(f"\nReport:\n{result.final_report}")