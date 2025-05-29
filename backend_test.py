import requests
import sys
import uuid
from datetime import datetime
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
        
        return success and 'stats' in response

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

    # Test geocoding
    tester.test_geocode("San Francisco, CA")

    # Test MCP endpoints
    tester.test_mcp_search_resources()
    tester.test_mcp_create_resource()
    tester.test_mcp_get_user_stats()

    # Test resource deletion
    tester.test_delete_resource()

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
