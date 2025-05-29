import requests
import sys
import uuid
from datetime import datetime, timedelta
import time

class GlobalHavenAPITester:
    def __init__(self, base_url="https://35f32e7d-5490-42ba-9e10-affcd9163446.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_resource_id = None
        self.test_water_source_id = None
        self.test_quality_report_id = None
        self.test_infrastructure_plan_id = None
        self.test_purification_guide_id = None
        self.test_water_alert_id = None
        self.mcp_api_key = "mcp-globalhaven-2025"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None, auth_type="bearer"):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_type == "bearer" and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        elif auth_type == "mcp":
            headers['Authorization'] = f'Bearer {self.mcp_api_key}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.text else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test(
            "API Root",
            "GET",
            "",
            200
        )

    def test_register(self, username, email, password):
        """Test user registration"""
        test_data = {
            "username": username,
            "email": email,
            "password": password,
            "full_name": "Test User",
            "phone": "123-456-7890",
            "location": {"lat": 37.7749, "lng": -122.4194}
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_data
        )
        
        if success:
            self.user_id = response.get('id')
            return True
        return False

    def test_login(self, username, password):
        """Test login and get token"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"username": username, "password": password}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_create_resource(self, title, description, category, type):
        """Test resource creation"""
        test_data = {
            "title": title,
            "description": description,
            "category": category,
            "type": type,
            "location": {"lat": 37.7749, "lng": -122.4194},
            "address": "123 Test Street, San Francisco, CA",
            "quantity": "5 units",
            "contact_info": "test@example.com"
        }
        
        success, response = self.run_test(
            "Create Resource",
            "POST",
            "resources",
            200,
            data=test_data
        )
        
        if success and 'id' in response:
            self.test_resource_id = response['id']
            return True
        return False

    def test_get_resources(self, category=None, type=None):
        """Test getting resources with optional filters"""
        params = {}
        if category:
            params['category'] = category
        if type:
            params['type'] = type
        
        success, response = self.run_test(
            f"Get Resources (filters: {params})",
            "GET",
            "resources",
            200,
            params=params
        )
        
        return success

    def test_get_resource_by_id(self):
        """Test getting a specific resource by ID"""
        if not self.test_resource_id:
            print("❌ No resource ID available for testing")
            return False
        
        success, _ = self.run_test(
            "Get Resource by ID",
            "GET",
            f"resources/{self.test_resource_id}",
            200
        )
        
        return success

    def test_update_resource(self):
        """Test updating a resource"""
        if not self.test_resource_id:
            print("❌ No resource ID available for testing")
            return False
        
        test_data = {
            "title": "Updated Test Resource",
            "description": "This resource has been updated",
            "category": "water",
            "type": "needed",
            "location": {"lat": 37.7749, "lng": -122.4194},
            "address": "456 Updated Street, San Francisco, CA",
            "quantity": "10 units",
            "contact_info": "updated@example.com"
        }
        
        success, _ = self.run_test(
            "Update Resource",
            "PUT",
            f"resources/{self.test_resource_id}",
            200,
            data=test_data
        )
        
        return success

    def test_delete_resource(self):
        """Test deleting a resource"""
        if not self.test_resource_id:
            print("❌ No resource ID available for testing")
            return False
        
        success, _ = self.run_test(
            "Delete Resource",
            "DELETE",
            f"resources/{self.test_resource_id}",
            200
        )
        
        return success

    def test_geocode(self, address):
        """Test geocoding functionality"""
        success, response = self.run_test(
            "Geocode Address",
            "GET",
            "geocode",
            200,
            params={"address": address}
        )
        
        return success and 'location' in response

    # Water Access Module Tests

    def test_create_water_source(self):
        """Test creating a water source"""
        test_data = {
            "name": "Test Well",
            "type": "well",
            "location": {"lat": 37.7749, "lng": -122.4194},
            "address": "123 Water Street, San Francisco, CA",
            "accessibility": "public",
            "quality_status": "unknown",
            "flow_rate": "10 L/min",
            "depth": 15.5,
            "treatment_required": True
        }
        
        success, response = self.run_test(
            "Create Water Source",
            "POST",
            "water/sources",
            200,
            data=test_data
        )
        
        if success and 'id' in response:
            self.test_water_source_id = response['id']
            return True
        return False

    def test_get_water_sources(self, type=None, accessibility=None, quality_status=None):
        """Test getting water sources with optional filters"""
        params = {}
        if type:
            params['type'] = type
        if accessibility:
            params['accessibility'] = accessibility
        if quality_status:
            params['quality_status'] = quality_status
        
        success, response = self.run_test(
            f"Get Water Sources (filters: {params})",
            "GET",
            "water/sources",
            200,
            params=params
        )
        
        return success

    def test_get_water_source_by_id(self):
        """Test getting a specific water source by ID"""
        if not self.test_water_source_id:
            print("❌ No water source ID available for testing")
            return False
        
        success, _ = self.run_test(
            "Get Water Source by ID",
            "GET",
            f"water/sources/{self.test_water_source_id}",
            200
        )
        
        return success

    def test_update_water_source(self):
        """Test updating a water source"""
        if not self.test_water_source_id:
            print("❌ No water source ID available for testing")
            return False
        
        test_data = {
            "name": "Updated Test Well",
            "type": "well",
            "location": {"lat": 37.7749, "lng": -122.4194},
            "address": "456 Updated Water Street, San Francisco, CA",
            "accessibility": "public",
            "quality_status": "safe",
            "flow_rate": "15 L/min",
            "depth": 20.0,
            "treatment_required": False
        }
        
        success, _ = self.run_test(
            "Update Water Source",
            "PUT",
            f"water/sources/{self.test_water_source_id}",
            200,
            data=test_data
        )
        
        return success

    def test_create_quality_report(self):
        """Test creating a water quality report"""
        if not self.test_water_source_id:
            print("❌ No water source ID available for testing")
            return False
            
        test_data = {
            "water_source_id": self.test_water_source_id,
            "test_type": "visual",
            "ph_level": 7.2,
            "turbidity": "clear",
            "color": "colorless",
            "odor": "none",
            "taste": "none",
            "bacteria_present": False,
            "chemical_contaminants": ["none"],
            "overall_rating": "safe",
            "notes": "Water appears clean and safe for consumption"
        }
        
        success, response = self.run_test(
            "Create Quality Report",
            "POST",
            "water/quality-reports",
            200,
            data=test_data
        )
        
        if success and 'id' in response:
            self.test_quality_report_id = response['id']
            return True
        return False

    def test_get_quality_reports(self, water_source_id=None):
        """Test getting quality reports with optional filters"""
        params = {}
        if water_source_id:
            params['water_source_id'] = water_source_id
        
        success, _ = self.run_test(
            f"Get Quality Reports (filters: {params})",
            "GET",
            "water/quality-reports",
            200,
            params=params
        )
        
        return success

    def test_create_infrastructure_plan(self):
        """Test creating an infrastructure plan"""
        test_data = {
            "title": "Test Well Drilling Project",
            "description": "A community well drilling project to provide clean water",
            "plan_type": "well_drilling",
            "location": {"lat": 37.7749, "lng": -122.4194},
            "estimated_cost": 5000.0,
            "currency": "USD",
            "materials_needed": ["drill", "pipes", "pump"],
            "tools_required": ["drilling equipment", "shovels"],
            "estimated_time": "2 weeks",
            "skill_level": "intermediate",
            "water_yield": "500 L/day",
            "serves_population": 100
        }
        
        success, response = self.run_test(
            "Create Infrastructure Plan",
            "POST",
            "water/infrastructure-plans",
            200,
            data=test_data
        )
        
        if success and 'id' in response:
            self.test_infrastructure_plan_id = response['id']
            return True
        return False

    def test_get_infrastructure_plans(self, plan_type=None, funding_status=None):
        """Test getting infrastructure plans with optional filters"""
        params = {}
        if plan_type:
            params['plan_type'] = plan_type
        if funding_status:
            params['funding_status'] = funding_status
        
        success, _ = self.run_test(
            f"Get Infrastructure Plans (filters: {params})",
            "GET",
            "water/infrastructure-plans",
            200,
            params=params
        )
        
        return success

    def test_create_purification_guide(self):
        """Test creating a purification guide"""
        test_data = {
            "title": "Simple Boiling Method",
            "description": "A guide to purify water through boiling",
            "method_type": "boiling",
            "local_materials": ["pot", "fuel", "container"],
            "steps": ["Collect water", "Bring to rolling boil", "Boil for 1 minute", "Let cool", "Store safely"],
            "time_required": "30 minutes",
            "effectiveness": "high",
            "suitable_for": ["bacteria", "viruses"],
            "region_specific": None,
            "cost_estimate": "Low cost",
            "difficulty_level": "beginner"
        }
        
        success, response = self.run_test(
            "Create Purification Guide",
            "POST",
            "water/purification-guides",
            200,
            data=test_data
        )
        
        if success and 'id' in response:
            self.test_purification_guide_id = response['id']
            return True
        return False

    def test_get_purification_guides(self, method_type=None, effectiveness=None, difficulty_level=None):
        """Test getting purification guides with optional filters"""
        params = {}
        if method_type:
            params['method_type'] = method_type
        if effectiveness:
            params['effectiveness'] = effectiveness
        if difficulty_level:
            params['difficulty_level'] = difficulty_level
        
        success, _ = self.run_test(
            f"Get Purification Guides (filters: {params})",
            "GET",
            "water/purification-guides",
            200,
            params=params
        )
        
        return success

    def test_get_purification_guide_by_id(self):
        """Test getting a specific purification guide by ID"""
        if not self.test_purification_guide_id:
            print("❌ No purification guide ID available for testing")
            return False
        
        success, _ = self.run_test(
            "Get Purification Guide by ID",
            "GET",
            f"water/purification-guides/{self.test_purification_guide_id}",
            200
        )
        
        return success

    def test_create_water_alert(self):
        """Test creating a water alert"""
        test_data = {
            "title": "Test Water Contamination Alert",
            "description": "Possible contamination in local water supply",
            "alert_type": "contamination",
            "severity": "medium",
            "location": {"lat": 37.7749, "lng": -122.4194},
            "radius_km": 5.0,
            "water_source_ids": [self.test_water_source_id] if self.test_water_source_id else [],
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        success, response = self.run_test(
            "Create Water Alert",
            "POST",
            "water/alerts",
            200,
            data=test_data
        )
        
        if success and 'id' in response:
            self.test_water_alert_id = response['id']
            return True
        return False

    def test_get_water_alerts(self, alert_type=None, severity=None):
        """Test getting water alerts with optional filters"""
        params = {}
        if alert_type:
            params['alert_type'] = alert_type
        if severity:
            params['severity'] = severity
        
        success, _ = self.run_test(
            f"Get Water Alerts (filters: {params})",
            "GET",
            "water/alerts",
            200,
            params=params
        )
        
        return success

    def test_verify_water_alert(self):
        """Test verifying a water alert"""
        if not self.test_water_alert_id:
            print("❌ No water alert ID available for testing")
            return False
        
        success, _ = self.run_test(
            "Verify Water Alert",
            "PUT",
            f"water/alerts/{self.test_water_alert_id}/verify",
            200
        )
        
        return success

    def test_log_water_usage(self):
        """Test logging water usage"""
        test_data = {
            "drinking_liters": 2.5,
            "cooking_liters": 5.0,
            "cleaning_liters": 10.0,
            "agriculture_liters": 0.0,
            "other_liters": 1.5,
            "source_ids": [self.test_water_source_id] if self.test_water_source_id else [],
            "notes": "Test water usage logging"
        }
        
        success, _ = self.run_test(
            "Log Water Usage",
            "POST",
            "water/usage",
            200,
            data=test_data
        )
        
        return success

    def test_get_water_usage(self):
        """Test getting water usage records"""
        success, _ = self.run_test(
            "Get Water Usage Records",
            "GET",
            "water/usage",
            200
        )
        
        return success

    def test_get_water_usage_stats(self):
        """Test getting water usage statistics"""
        success, response = self.run_test(
            "Get Water Usage Stats",
            "GET",
            "water/usage/stats",
            200
        )
        
        return success and 'personal' in response

    # MCP Water Module Tests
    def test_mcp_search_water_sources(self, type=None, accessibility=None):
        """Test MCP search water sources endpoint"""
        data = {
            "action": "search",
            "data": {}
        }
        
        if type:
            data["data"]["type"] = type
        if accessibility:
            data["data"]["accessibility"] = accessibility
        
        success, response = self.run_test(
            "MCP Search Water Sources",
            "POST",
            "mcp/search_water_sources",
            200,
            data=data,
            auth_type="mcp"
        )
        
        return success and 'water_sources' in response

    def test_mcp_get_water_alerts(self, alert_type=None, severity=None):
        """Test MCP get water alerts endpoint"""
        data = {
            "action": "search",
            "data": {}
        }
        
        if alert_type:
            data["data"]["alert_type"] = alert_type
        if severity:
            data["data"]["severity"] = severity
        
        success, response = self.run_test(
            "MCP Get Water Alerts",
            "POST",
            "mcp/get_water_alerts",
            200,
            data=data,
            auth_type="mcp"
        )
        
        return success and 'water_alerts' in response

    def test_mcp_get_purification_guides(self, method_type=None, effectiveness=None):
        """Test MCP get purification guides endpoint"""
        data = {
            "action": "search",
            "data": {}
        }
        
        if method_type:
            data["data"]["method_type"] = method_type
        if effectiveness:
            data["data"]["effectiveness"] = effectiveness
        
        success, response = self.run_test(
            "MCP Get Purification Guides",
            "POST",
            "mcp/get_purification_guides",
            200,
            data=data,
            auth_type="mcp"
        )
        
        return success and 'purification_guides' in response

    def test_mcp_create_water_source(self):
        """Test MCP water source creation"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        data = {
            "action": "create",
            "data": {
                "user_id": self.user_id,
                "name": "MCP Created Water Source",
                "type": "spring",
                "location": {"lat": 37.7749, "lng": -122.4194},
                "address": "789 MCP Water Street, San Francisco, CA",
                "accessibility": "public",
                "quality_status": "unknown"
            }
        }
        
        success, response = self.run_test(
            "MCP Create Water Source",
            "POST",
            "mcp/create_water_source",
            200,
            data=data,
            auth_type="mcp"
        )
        
        return success and 'water_source' in response

    def test_mcp_create_water_alert(self):
        """Test MCP water alert creation"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        data = {
            "action": "create",
            "data": {
                "user_id": self.user_id,
                "title": "MCP Created Water Alert",
                "description": "This alert was created via MCP",
                "alert_type": "supply_disruption",
                "severity": "medium",
                "location": {"lat": 37.7749, "lng": -122.4194},
                "radius_km": 3.0
            }
        }
        
        success, response = self.run_test(
            "MCP Create Water Alert",
            "POST",
            "mcp/create_water_alert",
            200,
            data=data,
            auth_type="mcp"
        )
        
        return success and 'water_alert' in response

    def test_mcp_log_water_usage(self):
        """Test MCP water usage logging"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        data = {
            "action": "log",
            "data": {
                "user_id": self.user_id,
                "drinking_liters": 3.0,
                "cooking_liters": 4.0,
                "cleaning_liters": 8.0,
                "agriculture_liters": 2.0,
                "other_liters": 1.0
            }
        }
        
        success, response = self.run_test(
            "MCP Log Water Usage",
            "POST",
            "mcp/log_water_usage",
            200,
            data=data,
            auth_type="mcp"
        )
        
        return success and 'water_usage' in response

    def test_mcp_search_resources(self, category=None, type=None):
        """Test MCP search resources endpoint"""
        data = {
            "action": "search",
            "data": {}
        }
        
        if category:
            data["data"]["category"] = category
        if type:
            data["data"]["type"] = type
        
        success, response = self.run_test(
            "MCP Search Resources",
            "POST",
            "mcp/search_resources",
            200,
            data=data,
            auth_type="mcp"
        )
        
        return success and 'resources' in response

    def test_mcp_create_resource(self):
        """Test MCP resource creation"""
        if not self.user_id:
            print("❌ No user ID available for testing")
            return False
        
        data = {
            "action": "create",
            "data": {
                "user_id": self.user_id,
                "title": "MCP Created Resource",
                "description": "This resource was created via MCP",
                "category": "food",
                "type": "available",
                "location": {"lat": 37.7749, "lng": -122.4194},
                "address": "789 MCP Street, San Francisco, CA",
                "quantity": "3 units",
                "contact_info": "mcp@example.com"
            }
        }
        
        success, response = self.run_test(
            "MCP Create Resource",
            "POST",
            "mcp/create_resource",
            200,
            data=data,
            auth_type="mcp"
        )
        
        return success and 'resource' in response

    def test_mcp_get_user_stats(self):
        """Test MCP get user stats endpoint"""
        data = {
            "action": "stats"
        }
        
        success, response = self.run_test(
            "MCP Get User Stats",
            "POST",
            "mcp/get_user_stats",
            200,
            data=data,
            auth_type="mcp"
        )
        
        return success and 'stats' in response and 'water_module' in response['stats']

def main():
    # Setup
    tester = GlobalHavenAPITester()
    timestamp = datetime.now().strftime('%H%M%S')
    test_username = f"testuser_{timestamp}"
    test_email = f"test_{timestamp}@example.com"
    test_password = "TestPass123!"

    # Test API root
    tester.test_api_root()

    # Test user registration and login
    if not tester.test_register(test_username, test_email, test_password):
        print("❌ Registration failed, stopping tests")
        return 1

    time.sleep(1)  # Small delay to ensure registration is processed

    if not tester.test_login(test_username, test_password):
        print("❌ Login failed, stopping tests")
        return 1

    # Test resource CRUD operations
    if not tester.test_create_resource(
        "Test Resource",
        "This is a test resource for API testing",
        "food",
        "available"
    ):
        print("❌ Resource creation failed, stopping tests")
        return 1

    tester.test_get_resources()
    tester.test_get_resources(category="food")
    tester.test_get_resources(type="available")
    tester.test_get_resource_by_id()
    tester.test_update_resource()

    # Test Water Access Module
    print("\n🌊 Testing Water Access Module...")

    # Test Water Sources
    if not tester.test_create_water_source():
        print("❌ Water source creation failed")
    else:
        tester.test_get_water_sources()
        tester.test_get_water_sources(type="well")
        tester.test_get_water_sources(accessibility="public")
        tester.test_get_water_source_by_id()
        tester.test_update_water_source()

    # Test Quality Reports
    tester.test_create_quality_report()
    tester.test_get_quality_reports()
    if tester.test_water_source_id:
        tester.test_get_quality_reports(water_source_id=tester.test_water_source_id)

    # Test Infrastructure Plans
    tester.test_create_infrastructure_plan()
    tester.test_get_infrastructure_plans()
    tester.test_get_infrastructure_plans(plan_type="well_drilling")

    # Test Purification Guides
    tester.test_create_purification_guide()
    tester.test_get_purification_guides()
    tester.test_get_purification_guides(method_type="boiling")
    tester.test_get_purification_guides(effectiveness="high")
    tester.test_get_purification_guide_by_id()

    # Test Water Alerts
    tester.test_create_water_alert()
    tester.test_get_water_alerts()
    tester.test_get_water_alerts(alert_type="contamination")
    tester.test_verify_water_alert()

    # Test Water Usage
    tester.test_log_water_usage()
    tester.test_get_water_usage()
    tester.test_get_water_usage_stats()

    # Test MCP Water Module Endpoints
    print("\n🤖 Testing MCP Water Module Integration...")
    tester.test_mcp_search_water_sources()
    tester.test_mcp_get_water_alerts()
    tester.test_mcp_get_purification_guides()
    tester.test_mcp_create_water_source()
    tester.test_mcp_create_water_alert()
    tester.test_mcp_log_water_usage()

    # Test other MCP endpoints
    tester.test_mcp_search_resources()
    tester.test_mcp_create_resource()
    tester.test_mcp_get_user_stats()

    # Test geocoding
    tester.test_geocode("San Francisco, CA")

    # Test resource deletion
    tester.test_delete_resource()

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
