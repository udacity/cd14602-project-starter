#!/bin/bash
# Validation script for all Lesson 5 exercises

echo "=================================================="
echo "Validating Lesson 5 Exercises"
echo "=================================================="
echo ""

total_tests=0
passed_tests=0
failed_concepts=()

# Concept 1
echo "=== CONCEPT 1: AI Planning Collaboration ==="
cd concept1-ai-planning-collaboration/solution
if pytest ../starter/test_planning_process.py -v --tb=no -q 2>&1 | tee /tmp/c1.out | grep -q "21 passed"; then
    echo "✅ Concept 1: 21/21 tests passed"
    passed_tests=$((passed_tests + 21))
else
    echo "❌ Concept 1: FAILED"
    failed_concepts+=("Concept 1")
fi
total_tests=$((total_tests + 21))
echo ""

# Concept 2
echo "=== CONCEPT 2: AI Code Generation ==="
cd ../../concept2-ai-code-generation/solution
if pytest test_transaction_loader.py test_report_modes.py -v --tb=no -q 2>&1 | tee /tmp/c2.out | grep -q "38 passed"; then
    echo "✅ Concept 2: 38/38 tests passed"
    passed_tests=$((passed_tests + 38))
else
    echo "❌ Concept 2: FAILED"
    failed_concepts+=("Concept 2")
fi
total_tests=$((total_tests + 38))
echo ""

# Concept 3
echo "=== CONCEPT 3: AI Test Creation ==="
cd ../../concept3-ai-test-creation/solution
if pytest test_report_engine.py validate_test_quality.py -v --tb=no -q 2>&1 | tee /tmp/c3.out | grep -q "27 passed"; then
    echo "✅ Concept 3: 27/27 tests passed"
    passed_tests=$((passed_tests + 27))
else
    echo "❌ Concept 3: FAILED"
    failed_concepts+=("Concept 3")
fi
total_tests=$((total_tests + 27))
echo ""

# Concept 4
echo "=== CONCEPT 4: AI Refactoring Collaboration ==="
cd ../../concept4-ai-refactoring-collaboration/solution
if pytest test_cli_interface.py -v --tb=no -q 2>&1 | tee /tmp/c4.out | grep -q "6 passed"; then
    echo "✅ Concept 4: 6/6 tests passed"
    passed_tests=$((passed_tests + 6))
else
    echo "❌ Concept 4: FAILED"
    failed_concepts+=("Concept 4")
fi
total_tests=$((total_tests + 6))
echo ""

# Concept 5
echo "=== CONCEPT 5: AI Documentation Generation ==="
cd ../../concept5-ai-documentation-generation/solution
if pytest test_documentation_quality.py -v --tb=no -q 2>&1 | tee /tmp/c5.out | grep -q "9 passed"; then
    echo "✅ Concept 5: 9/9 tests passed"
    passed_tests=$((passed_tests + 9))
else
    echo "❌ Concept 5: FAILED"
    failed_concepts+=("Concept 5")
fi
total_tests=$((total_tests + 9))
echo ""

echo "=================================================="
echo "VALIDATION SUMMARY"
echo "=================================================="
echo "Total Tests: $total_tests"
echo "Passed: $passed_tests"
echo "Failed: $((total_tests - passed_tests))"
echo ""

if [ ${#failed_concepts[@]} -eq 0 ]; then
    echo "✅ ALL EXERCISES VALIDATED SUCCESSFULLY!"
    exit 0
else
    echo "❌ Failed concepts: ${failed_concepts[*]}"
    exit 1
fi
