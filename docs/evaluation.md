Dataset size: 4 questions.
Retrieval Hit Rate@1: 100%.
Retrieval Hit Rate@3: 100%.
MRR: 1.0000.
Any incorrect, incomplete, or unsupported generated answers you observe.


## Automated Debugging Benchmark

The debugging benchmark evaluates the complete AI debugging workflow.

It measures:

- Patch generation success
- Expected source retrieval
- Correct target file selection
- Expected correction generation
- Test execution success
- End-to-end workflow success

### Running the benchmark

```bash
python -m scripts.evaluate_debugging_workflow