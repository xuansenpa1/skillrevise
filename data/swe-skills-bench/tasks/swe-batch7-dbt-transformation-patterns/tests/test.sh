#!/usr/bin/env bash
set -uo pipefail

mkdir -p /logs/verifier /tmp/benchmark_tests
cp /tests/test_dbt_transformation_patterns.py /tmp/benchmark_tests/test_dbt_transformation_patterns.py
if [ -f /tests/_dependency_utils.py ]; then cp /tests/_dependency_utils.py /tmp/benchmark_tests/_dependency_utils.py; fi
if ! python -m pytest --version >/dev/null 2>&1; then
  python -m pip install pytest -q --break-system-packages >/logs/verifier/pip_pytest.log 2>&1 || \
    python -m pip install pytest -q >/logs/verifier/pip_pytest.log 2>&1
fi

reward=1
if [ "$reward" -eq 1 ]; then
  echo '[swe-skills-bench] unit_test 0: python -m pytest /tmp/benchmark_tests/test_dbt_transformation_patterns.py -v --tb=short' | tee -a /logs/verifier/test_output.log
  cd /tmp/benchmark_tests && unset PYTHONPATH
  python -m pytest /tmp/benchmark_tests/test_dbt_transformation_patterns.py -v --tb=short 2>&1 | tee -a /logs/verifier/test_output.log
  status=${PIPESTATUS[0]}
  if [ "$status" -ne 0 ]; then reward=0; fi
fi

echo "$reward" > /logs/verifier/reward.txt
exit 0
