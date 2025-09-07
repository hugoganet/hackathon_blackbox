#!/usr/bin/env python3
"""
Test runner for Mentor Agent validation.

Provides convenient commands to run different test suites and generate reports.
"""

import sys
import subprocess
import argparse
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Duration: {end_time - start_time:.2f} seconds")
    
    if result.stdout:
        print("\nOutput:")
        print(result.stdout)
    
    if result.stderr:
        print("\nErrors:")
        print(result.stderr)
    
    success = result.returncode == 0
    status = "PASSED ✅" if success else "FAILED ❌"
    print(f"\nStatus: {status}")
    
    return success

def main():
    parser = argparse.ArgumentParser(description="Run Mentor Agent tests")
    parser.add_argument(
        "--suite",
        choices=["all", "agent", "tools", "requirements", "integration", "quick"],
        default="all",
        help="Test suite to run"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--verbose",
        action="store_true", 
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    args = parser.parse_args()
    
    # Base directory for tests
    test_dir = Path(__file__).parent
    agent_dir = test_dir.parent
    
    print("Mentor Agent Test Runner")
    print("="*60)
    print(f"Test Directory: {test_dir}")
    print(f"Agent Directory: {agent_dir}")
    
    # Build pytest command
    base_cmd = ["pytest"]
    
    if args.coverage:
        base_cmd.extend(["--cov=agents.mentor_agent", "--cov-report=html", "--cov-report=term"])
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.parallel:
        base_cmd.extend(["-n", "auto"])
    
    # Test suite selection
    test_files = {
        "agent": "test_agent.py",
        "tools": "test_tools.py", 
        "requirements": "test_requirements.py",
        "integration": "test_integration.py"
    }
    
    results = {}
    total_start_time = time.time()
    
    if args.suite == "all":
        # Run all test suites
        for suite_name, test_file in test_files.items():
            cmd = " ".join(base_cmd + [str(test_dir / test_file)])
            results[suite_name] = run_command(cmd, f"{suite_name.title()} Tests")
    
    elif args.suite == "quick":
        # Run quick smoke tests
        quick_tests = [
            "test_agent.py::TestMentorAgentBasics::test_agent_initialization",
            "test_tools.py::TestMemorySearch::test_memory_search_successful",
            "test_requirements.py::TestCoreFeatureRequirements::test_req_memory_guided_socratic_questions"
        ]
        
        for test in quick_tests:
            cmd = " ".join(base_cmd + [str(test_dir / test)])
            test_name = test.split("::")[-1]
            results[test_name] = run_command(cmd, f"Quick Test: {test_name}")
    
    else:
        # Run specific suite
        if args.suite in test_files:
            cmd = " ".join(base_cmd + [str(test_dir / test_files[args.suite])])
            results[args.suite] = run_command(cmd, f"{args.suite.title()} Tests")
        else:
            print(f"Unknown test suite: {args.suite}")
            sys.exit(1)
    
    total_end_time = time.time()
    
    # Summary report
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, success in results.items():
        status = "PASSED ✅" if success else "FAILED ❌"
        print(f"{test_name:<20}: {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    print(f"Total Runtime: {total_end_time - total_start_time:.2f} seconds")
    
    if args.coverage:
        print(f"\nCoverage report generated in: {agent_dir / 'htmlcov'}")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()