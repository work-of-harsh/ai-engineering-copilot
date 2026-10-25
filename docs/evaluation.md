Dataset size: 4 questions.
Retrieval Hit Rate@1: 100%.
Retrieval Hit Rate@3: 100%.
MRR: 1.0000.
Any incorrect, incomplete, or unsupported generated answers you observe.



25-10-2026

Question 1: Where is percentage-based tax calculated?
Expected source: app/payment.py
  1. config\README.md | similarity=0.5901
  2. app\payment.py | similarity=0.6679
  3. tests\test_payment.py | similarity=0.6644
Result: HIT at rank 2

Question 2: Which function decides whether a payment is allowed?
Expected source: app/payment.py
  1. tests\test_payment.py | similarity=0.6859
  2. config\README.md | similarity=0.6207
  3. app\payment.py | similarity=0.7031
Result: HIT at rank 3

Question 3: Where are payment timeout and retry settings stored?
Expected source: config/payment.yaml
  1. config\payment.yaml | similarity=0.8002
  2. config\README.md | similarity=0.6200
  3. tests\test_payment.py | similarity=0.5737
Result: HIT at rank 1

Question 4: Where are the payment unit tests defined?
Expected source: tests/test_payment.py
  1. config\README.md | similarity=0.7182
  2. tests\test_payment.py | similarity=0.7476
  3. config\payment.yaml | similarity=0.6755
Result: HIT at rank 2

--- Retrieval Evaluation Summary ---
Questions: 4
Hit Rate@1: 25.00%
Hit Rate@3: 100.00%
MRR: 0.5833
