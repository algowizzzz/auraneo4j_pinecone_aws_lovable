#!/usr/bin/env python3
"""
Test Runner for SEC Graph LangGraph Agent
Executes comprehensive test suite and provides detailed reporting
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import argparse

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED ({duration:.1f}s)")
            if result.stdout:
                print(f"📋 Output:\n{result.stdout}")
            return True
        else:
            print(f"❌ {description} - FAILED ({duration:.1f}s)")
            if result.stdout:
                print(f"📋 Output:\n{result.stdout}")
            if result.stderr:
                print(f"🚨 Error:\n{result.stderr}")
            return False
            
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'pytest',
        'pytest-asyncio', 
        'pytest-mock',
        'neo4j',
        'sentence_transformers',
        'pinecone',
        'langchain',
        'langgraph',
        'openai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def run_test_phase(phase_name, test_files, args):
    """Run a specific test phase"""
    print(f"\n🚀 Starting {phase_name}")
    
    success_count = 0
    total_count = len(test_files)
    
    for test_file in test_files:
        test_path = f"tests/{test_file}"
        
        if not os.path.exists(test_path):
            print(f"⚠️  Test file {test_file} not found, skipping...")
            continue
        
        # Build pytest command
        cmd_parts = ["python", "-m", "pytest", test_path]
        
        if args.verbose:
            cmd_parts.append("-v")
        if args.capture == 'no':
            cmd_parts.append("-s")
        if args.tb:
            cmd_parts.extend(["--tb", args.tb])
        if args.markers:
            cmd_parts.extend(["-m", args.markers])
        
        cmd = " ".join(cmd_parts)
        
        if run_command(cmd, f"Running {test_file}"):
            success_count += 1
    
    print(f"\n📊 {phase_name} Results: {success_count}/{total_count} tests passed")
    return success_count == total_count

def generate_coverage_report(args):
    """Generate test coverage report"""
    if not args.coverage:
        return True
    
    cmd = "python -m pytest tests/ --cov=agent --cov=data_pipeline --cov-report=html --cov-report=term"
    return run_command(cmd, "Generating coverage report")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="SEC Graph Test Runner")
    parser.add_argument("--phase", choices=["1", "2", "3", "4", "all"], default="all",
                       help="Test phase to run (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--coverage", action="store_true",
                       help="Generate coverage report")
    parser.add_argument("--capture", choices=["no", "sys"], default="sys",
                       help="Capture output mode")
    parser.add_argument("--tb", choices=["short", "long", "line", "native"], default="short",
                       help="Traceback format")
    parser.add_argument("--markers", help="Run tests with specific markers")
    parser.add_argument("--skip-deps", action="store_true",
                       help="Skip dependency check")
    
    args = parser.parse_args()
    
    print("🔬 SEC Graph LangGraph Agent - Test Suite")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check dependencies
    if not args.skip_deps and not check_dependencies():
        print("\n❌ Dependency check failed. Fix dependencies and try again.")
        return 1
    
    # Define test phases
    test_phases = {
        "1": {
            "name": "Phase 1: Technical Infrastructure",
            "files": [
                "test_01_environment.py",
                "test_02_data_pipeline.py", 
                "test_03_langgraph_infrastructure.py"
            ]
        },
        "2": {
            "name": "Phase 2: Component-Level Testing",
            "files": [
                "test_04_individual_nodes.py",
                "test_05_enhanced_integration.py"
            ]
        },
        "3": {
            "name": "Phase 3: Business Use Cases",
            "files": [
                "test_06_sec_core_queries.py",
                "test_07_advanced_analysis.py",
                "test_08_complex_scenarios.py"
            ]
        },
        "4": {
            "name": "Phase 4: Performance & Integration",
            "files": [
                "test_09_performance.py",
                "test_10_error_handling.py"
            ]
        }
    }
    
    # Run selected phases
    phases_to_run = []
    if args.phase == "all":
        phases_to_run = ["1", "2", "3", "4"]
    else:
        phases_to_run = [args.phase]
    
    total_success = True
    
    for phase_num in phases_to_run:
        if phase_num in test_phases:
            phase_info = test_phases[phase_num]
            phase_success = run_test_phase(phase_info["name"], phase_info["files"], args)
            total_success = total_success and phase_success
        else:
            print(f"⚠️  Unknown phase: {phase_num}")
    
    # Generate coverage report if requested
    if args.coverage:
        generate_coverage_report(args)
    
    # Final summary
    print(f"\n{'='*60}")
    print("📋 FINAL TEST SUMMARY")
    print(f"{'='*60}")
    
    if total_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ System is ready for production deployment")
        return_code = 0
    else:
        print("⚠️  SOME TESTS FAILED")
        print("🔧 Review failed tests and fix issues before deployment")
        return_code = 1
    
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return return_code

if __name__ == "__main__":
    sys.exit(main())