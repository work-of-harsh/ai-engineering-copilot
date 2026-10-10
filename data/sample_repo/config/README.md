# Sample Payment Application

A fictional payment service used to test AI Engineering Copilot.

## Components

- app/payment.py: Payment calculation and validation
- tests/test_payment.py: Unit tests for payment functionality
- config/payment.yaml: Payment timeout and retry configuration

## Known Issue

The calculate_total function does not correctly calculate
percentage-based tax.