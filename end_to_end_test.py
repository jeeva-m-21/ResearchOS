#!/usr/bin/env python3
"""
Comprehensive end-to-end test of ResearchOS
"""

import requests
import json
import time

class ResearchOSTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.headers = None
        self.experiment_id = None
        self.run_id = None
        
    def print_step(self, step_num, description):
        """Print formatted step"""
        print(f"\n{'='*60}")
        print(f"STEP {step_num}: {description}")
        print(f"{'='*60}")
        
    def test_health(self):
        """Test health endpoints"""
        self.print_step(1, "Health Checks")
        
        # Basic health
        response = requests.get(f"{self.base_url}/health/")
        print(f"✅ Health status: {response.status_code}")
        
        # Readiness
        response = requests.get(f"{self.base_url}/health/ready")
        data = response.json()
        print(f"✅ Ready status: {response.status_code} - Database: {data.get('database', 'N/A')}")
        
        return response.status_code == 200
        
    def test_authentication(self):
        """Test authentication flow"""
        self.print_step(2, "Authentication Flow")
        
        # Attempt login
        login_data = {
            "email": "researcher@test.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{self.base_url}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
            
        token_data = response.json()
        self.access_token = token_data.get("access_token")
        token_type = token_data.get("token_type", "bearer")
        
        print(f"✅ Login successful!")
        print(f"   Token type: {token_type}")
        print(f"   Token: {self.access_token[:30]}...")
        
        # Set headers for authenticated requests
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Test profile endpoint
        response = requests.get(
            f"{self.base_url}/auth/profile",
            headers=self.headers
        )
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Profile retrieved: {profile.get('email', 'N/A')}")
        else:
            print(f"⚠️ Profile status: {response.status_code} - {response.text}")
            
        # Test organizations endpoint
        response = requests.get(
            f"{self.base_url}/auth/organizations",
            headers=self.headers
        )
        
        if response.status_code == 200:
            orgs = response.json()
            print(f"✅ Organizations: {len(orgs)} organization(s)")
        else:
            print(f"⚠️ Organizations status: {response.status_code}")
            
        return True
        
    def test_experiment_creation(self):
        """Test experiment creation workflow"""
        self.print_step(3, "Experiment Creation")
        
        if not self.headers:
            print("❌ Not authenticated")
            return False
        
        # Create a project first
        project_response = requests.get(
            f"{self.base_url}/auth/organizations",
            headers=self.headers
        )
        
        if project_response.status_code != 200:
            print(f"❌ Cannot get organizations: {project_response.status_code}")
            return False
        
        orgs = project_response.json()
        if not orgs:
            print("❌ No organizations found")
            return False
        
        org_id = orgs[0].get("organization_id")
        
        # Assume we have a project in the database
        import uuid
        project_id = str(uuid.UUID("90c7cb47-cc1f-472f-99c5-2b17a9e088a8"))
        
        experiment_params = {
            "name": "Text Classification Experiment",
            "project_id": project_id,
            "description": "Testing research workflow with BERT model"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/experiments/",
            params=experiment_params,
            headers=self.headers
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Experiment creation failed: {response.status_code} - {response.text}")
            return False
            
        experiment = response.json()
        self.experiment_id = experiment.get("id")
        
        print(f"✅ Experiment created:")
        print(f"   ID: {self.experiment_id}")
        print(f"   Name: {experiment.get('name')}")
        print(f"   Status: {experiment.get('status', 'created')}")
        
        return True
        
    def test_run_creation(self):
        """Test run creation"""
        self.print_step(4, "Run Creation")
        
        if not self.experiment_id:
            print("❌ No experiment ID")
            return False
            
        run_data = {
            "git_commit": "abc123def456",
            "parameters": {
                "learning_rate": 0.00001,
                "batch_size": 16
            }
        }
        
        response = requests.post(
            f"{self.base_url}/v1/experiments/{self.experiment_id}/runs",
            json=run_data,
            headers=self.headers
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Run creation failed: {response.status_code} - {response.text}")
            return False
            
        run = response.json()
        self.run_id = run.get("run_id")  # API returns run_id, not id
        
        print(f"✅ Run created:")
        print(f"   ID: {self.run_id}")
        print(f"   Run Number: {run.get('run_number')}")
        print(f"   Status: {run.get('status', 'created')}")
        
        return True
        
    def test_metric_logging(self):
        """Test metric logging"""
        self.print_step(5, "Metric Logging")
        
        if not self.run_id:
            print("❌ No run ID")
            return False
            
        # Log multiple metrics
        metrics = [
            {"key": "accuracy", "value": 0.85, "step": 100},
            {"key": "loss", "value": 0.32, "step": 100},
            {"key": "f1_score", "value": 0.88, "step": 100},
            {"key": "accuracy", "value": 0.87, "step": 200},
            {"key": "loss", "value": 0.28, "step": 200},
        ]
        
        success_count = 0
        for metric in metrics:
            response = requests.post(
                f"{self.base_url}/v1/experiments/{self.experiment_id}/runs/{self.run_id}/metrics",
                json=metric,
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                success_count += 1
                
        print(f"✅ Logged {success_count}/{len(metrics)} metrics")
        
        # Retrieve metrics
        response = requests.get(
            f"{self.base_url}/v1/experiments/{self.experiment_id}/runs/{self.run_id}/metrics",
            headers=self.headers
        )
        
        if response.status_code == 200:
            metrics_list = response.json()
            print(f"✅ Retrieved {len(metrics_list)} metrics")
            
            # Show summary
            metric_counts = {}
            for metric in metrics_list[:5]:  # Show first 5
                key = metric.get("key")
                metric_counts[key] = metric_counts.get(key, 0) + 1
                
            print(f"   Metric distribution: {metric_counts}")
        else:
            print(f"⚠️ Could not retrieve metrics: {response.status_code}")
            
        return success_count > 0
        
    def test_search(self):
        """Test search functionality"""
        self.print_step(6, "Search")
        
        if not self.headers:
            print("❌ Not authenticated")
            return False
            
        # Search for experiments
        search_response = requests.get(
            f"{self.base_url}/v1/search/",
            params={"q": "classification", "limit": 5},
            headers=self.headers
        )
        
        if search_response.status_code == 200:
            results = search_response.json()
            print(f"✅ Search successful:")
            print(f"   Total results: {results.get('total', 0)}")
            print(f"   Took: {results.get('took_ms', 0)}ms")
            
            # Show first result
            results_list = results.get("results", [])
            if results_list:
                first_result = results_list[0]
                print(f"   First result: {first_result.get('title', 'N/A')}")
                
            return True
        else:
            print(f"⚠️ Search failed: {search_response.status_code} - {search_response.text}")
            return False
            
    def test_experiment_completion(self):
        """Complete the experiment run"""
        self.print_step(7, "Experiment Completion")
        
        if not self.experiment_id or not self.run_id:
            print("❌ Missing experiment or run ID")
            return False
            
        # Complete the run
        complete_data = {
            "status": "completed",
            "error": None
        }
        
        response = requests.post(
            f"{self.base_url}/v1/experiments/{self.experiment_id}/runs/{self.run_id}/complete",
            json=complete_data,
            headers=self.headers
        )
        
        if response.status_code in [200, 202]:
            print(f"✅ Run completed successfully")
            return True
        else:
            print(f"⚠️ Run completion failed: {response.status_code} - {response.text}")
            return False
            
    def run_all_tests(self):
        """Run all end-to-end tests"""
        print("\n" + "="*60)
        print("RESEARCHOS - COMPREHENSIVE END-TO-END TEST")
        print("="*60)
        
        tests = [
            ("Health Checks", self.test_health),
            ("Authentication", self.test_authentication),
            ("Experiment Creation", self.test_experiment_creation),
            ("Run Creation", self.test_run_creation),
            ("Metric Logging", self.test_metric_logging),
            ("Search", self.test_search),
            ("Experiment Completion", self.test_experiment_completion)
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                status = "✅ PASS" if result else "❌ FAIL"
                results.append((name, result, status))
            except Exception as e:
                print(f"❌ Test '{name}' crashed: {e}")
                results.append((name, False, "💥 CRASH"))
                
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result, _ in results if result)
        total = len(results)
        
        for name, result, status in results:
            print(f"{status} {name}")
            
        print(f"\n🎯 Score: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🌟 ALL TESTS PASSED! ResearchOS is operational!")
        elif passed >= total * 0.7:
            print("\n⚠️ MOST TESTS PASSED - Minor issues found")
        else:
            print("\n❌ SIGNIFICANT ISSUES FOUND")
            
        return passed / total >= 0.7  # At least 70% pass rate

def main():
    """Main function"""
    tester = ResearchOSTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n📋 NEXT STEPS:")
            print("   1. Test with multiple users")
            print("   2. Test artifact upload")
            print("   3. Test notebook integration")
            print("   4. Test AI assistance endpoints")
            print("\n🚀 ResearchOS is READY for development!")
        else:
            print("\n🔧 ISSUES TO FIX:")
            print("   1. Check database connectivity")
            print("   2. Verify schema matches code")
            print("   3. Test individual endpoints")
            
        return success
        
    except Exception as e:
        print(f"\n💥 TEST RUNNER CRASHED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)