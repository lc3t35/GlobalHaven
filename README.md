# GlobalHaven Community Resource Hub

## Overview

GlobalHaven is a mobile-first community resource sharing platform that addresses fundamental human needs across six critical domains: water, food, shelter, safety, health, and economic security.

## 🌟 Key Features Implemented

### 1. Community Resource Sharing

- **Resource Posting**: Users can share available resources or post what they need
- **Smart Search**: Filter by category, type, and location with radius-based searching
- **Global Mapping**: OpenStreetMap integration with geocoding support
- **Real-time Updates**: Live resource feed with mobile-optimized interface

### 2. Mobile-First Design

- **Responsive UI**: Optimized for smartphones and basic devices
- **Touch-Friendly**: Large buttons and easy navigation
- **Offline Capability**: Core features work with minimal connectivity
- **Progressive Enhancement**: Works on low-spec devices

### 3. MCP Server Integration (LLM Access)

- **Natural Language Interface**: LLMs can interact with the platform
- **Resource Search**: AI can find resources using natural language queries
- **Resource Creation**: AI can post resources on behalf of users
- **Community Stats**: AI can access platform analytics

## 🚀 Live Demo

**Application URL**: https://35f32e7d-5490-42ba-9e10-affcd9163446.preview.emergentagent.com

### Quick Test Flow:

1. Visit the home page
2. Click "Join the Community"
3. Register with a new account
4. Create your first resource (food, water, tools, etc.)
5. Search and filter resources in your area

## 🤖 MCP Integration for LLMs

### Authentication

```bash
Authorization: Bearer mcp-globalhaven-2025
```

### Claude integration

Copy mcp/globalhaven-mcp.js to /users/path/to/

Add this configuration to claude_desktop_config.json mcpservers

````json
"mcpServers": {
  "globalhaven": {
      "command": "node",
      "args": ["/users/path/to/globalhaven-mcp.js"]
    }
}

### Available Endpoints

#### 1. Search Resources
```bash
POST /api/mcp/search_resources
{
  "action": "search_resources",
  "data": {
    "category": "food",
    "type": "available",
    "lat": 40.7128,
    "lng": -74.0060,
    "radius": 10
  }
}
````

#### 2. Create Resource

```bash
POST /api/mcp/create_resource
{
  "action": "create_resource",
  "data": {
    "user_id": "user-123",
    "title": "Fresh Vegetables",
    "description": "Organic vegetables from my garden",
    "category": "food",
    "type": "available",
    "location": {"lat": 40.7128, "lng": -74.0060},
    "address": "123 Main St, New York, NY"
  }
}
```

#### 3. Get Community Stats

```bash
POST /api/mcp/get_user_stats
{
  "action": "get_stats"
}
```

### Example LLM Interactions

**User**: "Find available water sources near San Francisco"
**LLM** → Search resources with category="water", type="available", lat=37.7749, lng=-122.4194

**User**: "I have 10 sleeping bags to donate in NYC"  
**LLM** → Create resource with category="shelter", type="available", location="NYC"

**User**: "How many people are using GlobalHaven?"
**LLM** → Get community stats

## 🔧 Technical Architecture

### Frontend

- **React 18** with mobile-first Tailwind CSS
- **React Leaflet** for OpenStreetMap integration
- **Axios** for API communication
- **Responsive design** for all device sizes

### Backend

- **FastAPI** with async support
- **MongoDB** with Motor driver
- **JWT Authentication** with bcrypt
- **OpenStreetMap Geocoding** via Nominatim
- **CORS enabled** for cross-origin requests

### Security

- **Bcrypt password hashing**
- **JWT token authentication**
- **API key protection** for MCP endpoints
- **Input validation** with Pydantic models

## 📱 Resource Categories

1. **🍎 Food**: Surplus food, meals, nutrition resources
2. **💧 Water**: Clean water sources, purification methods
3. **🔧 Tools**: Equipment sharing, skill exchanges
4. **🏠 Shelter**: Housing, building materials, designs
5. **🏥 Medical**: Healthcare resources, first aid
6. **💡 Skills**: Knowledge sharing, tutoring, services
7. **📦 Other**: Miscellaneous community resources

## 🌍 Global Impact Potential

This MVP demonstrates the core concept of a unified platform for addressing human needs:

- **Network Effects**: More valuable as community grows
- **Cross-Category Solutions**: One platform for multiple needs
- **AI Integration**: Natural language access through LLMs
- **Scalable Architecture**: Ready for global deployment
- **Community-Driven**: Democratic resource allocation

## 🔮 Next Steps for Enhancement

1. **Advanced Mapping**: Heat maps, route optimization
2. **Offline Sync**: Full offline capability with sync
3. **Messaging System**: Real-time chat between users
4. **Verification System**: Trust scores and reviews
5. **AI Matching**: Smart resource-need matching
6. **Multi-language**: Support for global communities
7. **Emergency Features**: Disaster response coordination

## 🎯 The "Aha Moment"

**GlobalHaven proves that addressing humanity's most fundamental needs doesn't require complex, siloed solutions. Instead, a simple, unified platform can create powerful network effects where sharing water sources connects to food distribution, which connects to shelter building, which connects to skill sharing - creating a resilient community ecosystem that grows stronger with every participant.**

The MCP integration makes this accessible to anyone through natural language, democratizing access to community resources through AI assistants.

---

_Built with ❤️ for global community resilience_
