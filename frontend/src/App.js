import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Set up axios defaults
axios.defaults.headers.common['Content-Type'] = 'application/json';

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [resources, setResources] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [userLocation, setUserLocation] = useState(null);

  // Categories for resources
  const categories = ['food', 'water', 'tools', 'skills', 'shelter', 'medical', 'other'];
  const types = ['available', 'needed'];

  // Set auth header when token changes
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      localStorage.setItem('token', token);
    } else {
      delete axios.defaults.headers.common['Authorization'];
      localStorage.removeItem('token');
    }
  }, [token]);

  // Get user location
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => console.log('Location access denied:', error)
      );
    }
  }, []);

  // Load resources when authenticated
  useEffect(() => {
    if (token) {
      loadResources();
    }
  }, [token, selectedCategory, selectedType]);

  const loadResources = async () => {
    try {
      const params = {};
      if (selectedCategory !== 'all') params.category = selectedCategory;
      if (selectedType !== 'all') params.type = selectedType;
      if (userLocation) {
        params.lat = userLocation.lat;
        params.lng = userLocation.lng;
        params.radius = 50; // 50km radius
      }

      const response = await axios.get(`${API}/resources`, { params });
      setResources(response.data);
    } catch (error) {
      console.error('Error loading resources:', error);
    }
  };

  const LoginForm = () => {
    const [loginData, setLoginData] = useState({ username: '', password: '' });
    const [isRegistering, setIsRegistering] = useState(false);
    const [registerData, setRegisterData] = useState({
      username: '', email: '', password: '', full_name: '', phone: ''
    });

    const handleLogin = async (e) => {
      e.preventDefault();
      try {
        const response = await axios.post(`${API}/auth/login`, loginData);
        setToken(response.data.access_token);
        setCurrentView('resources');
      } catch (error) {
        alert('Login failed: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    const handleRegister = async (e) => {
      e.preventDefault();
      try {
        const regData = { ...registerData };
        if (userLocation) {
          regData.location = userLocation;
        }
        await axios.post(`${API}/auth/register`, regData);
        alert('Registration successful! Please login.');
        setIsRegistering(false);
      } catch (error) {
        alert('Registration failed: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    if (isRegistering) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
            <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Join GlobalHaven</h2>
            <form onSubmit={handleRegister} className="space-y-4">
              <input
                type="text"
                placeholder="Username"
                value={registerData.username}
                onChange={(e) => setRegisterData({...registerData, username: e.target.value})}
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
              <input
                type="email"
                placeholder="Email"
                value={registerData.email}
                onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={registerData.password}
                onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
              <input
                type="text"
                placeholder="Full Name (optional)"
                value={registerData.full_name}
                onChange={(e) => setRegisterData({...registerData, full_name: e.target.value})}
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
              <input
                type="tel"
                placeholder="Phone (optional)"
                value={registerData.phone}
                onChange={(e) => setRegisterData({...registerData, phone: e.target.value})}
                className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
              <button
                type="submit"
                className="w-full bg-green-600 text-white py-4 rounded-xl font-semibold hover:bg-green-700 transition duration-200"
              >
                Register
              </button>
            </form>
            <p className="text-center mt-6 text-gray-600">
              Already have an account?{' '}
              <button
                onClick={() => setIsRegistering(false)}
                className="text-green-600 font-semibold hover:text-green-800"
              >
                Sign in
              </button>
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
          <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Welcome to GlobalHaven</h2>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="text"
              placeholder="Username"
              value={loginData.username}
              onChange={(e) => setLoginData({...loginData, username: e.target.value})}
              className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={loginData.password}
              onChange={(e) => setLoginData({...loginData, password: e.target.value})}
              className="w-full p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
              required
            />
            <button
              type="submit"
              className="w-full bg-green-600 text-white py-4 rounded-xl font-semibold hover:bg-green-700 transition duration-200"
            >
              Sign In
            </button>
          </form>
          <p className="text-center mt-6 text-gray-600">
            Don't have an account?{' '}
            <button
              onClick={() => setIsRegistering(true)}
              className="text-green-600 font-semibold hover:text-green-800"
            >
              Register
            </button>
          </p>
        </div>
      </div>
    );
  };

  const ResourceForm = ({ onClose, onSubmit }) => {
    const [formData, setFormData] = useState({
      title: '',
      description: '',
      category: 'food',
      type: 'available',
      location: userLocation || { lat: 0, lng: 0 },
      address: '',
      quantity: '',
      contact_info: ''
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/resources`, formData);
        onSubmit();
        onClose();
      } catch (error) {
        alert('Error creating resource: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    const handleGeocodeAddress = async () => {
      if (!formData.address) return;
      try {
        const response = await axios.get(`${API}/geocode`, { params: { address: formData.address } });
        setFormData({ ...formData, location: response.data.location });
        alert('Address geocoded successfully!');
      } catch (error) {
        alert('Could not geocode address');
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
          <h3 className="text-2xl font-bold text-gray-800 mb-6">Share a Resource</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              placeholder="Resource Title"
              value={formData.title}
              onChange={(e) => setFormData({...formData, title: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              required
            />
            
            <textarea
              placeholder="Description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 h-24"
              required
            />

            <select
              value={formData.category}
              onChange={(e) => setFormData({...formData, category: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
              ))}
            </select>

            <select
              value={formData.type}
              onChange={(e) => setFormData({...formData, type: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            >
              <option value="available">Available to Give</option>
              <option value="needed">Looking For</option>
            </select>

            <div className="space-y-2">
              <input
                type="text"
                placeholder="Address (optional)"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <button
                type="button"
                onClick={handleGeocodeAddress}
                className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 transition duration-200"
              >
                Get Coordinates from Address
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                step="0.000001"
                placeholder="Latitude"
                value={formData.location.lat}
                onChange={(e) => setFormData({...formData, location: {...formData.location, lat: parseFloat(e.target.value) || 0}})}
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
              <input
                type="number"
                step="0.000001"
                placeholder="Longitude"
                value={formData.location.lng}
                onChange={(e) => setFormData({...formData, location: {...formData.location, lng: parseFloat(e.target.value) || 0}})}
                className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>

            <input
              type="text"
              placeholder="Quantity/Amount (optional)"
              value={formData.quantity}
              onChange={(e) => setFormData({...formData, quantity: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            />

            <input
              type="text"
              placeholder="Contact Info (optional)"
              value={formData.contact_info}
              onChange={(e) => setFormData({...formData, contact_info: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
            />

            <div className="flex space-x-3 pt-4">
              <button
                type="submit"
                className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition duration-200"
              >
                Share Resource
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-gray-500 text-white py-3 rounded-lg font-semibold hover:bg-gray-600 transition duration-200"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const ResourceCard = ({ resource }) => {
    const typeColor = resource.type === 'available' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800';
    const categoryIcons = {
      food: '🍎', water: '💧', tools: '🔧', skills: '💡', 
      shelter: '🏠', medical: '🏥', other: '📦'
    };

    return (
      <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow duration-200">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">{categoryIcons[resource.category] || '📦'}</span>
            <h3 className="font-bold text-lg text-gray-800">{resource.title}</h3>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${typeColor}`}>
            {resource.type}
          </span>
        </div>
        
        <p className="text-gray-600 mb-3 text-sm">{resource.description}</p>
        
        <div className="space-y-2 text-sm text-gray-500">
          <div className="flex items-center space-x-2">
            <span>📍</span>
            <span>{resource.address || `${resource.location.lat.toFixed(4)}, ${resource.location.lng.toFixed(4)}`}</span>
          </div>
          
          {resource.quantity && (
            <div className="flex items-center space-x-2">
              <span>📊</span>
              <span>{resource.quantity}</span>
            </div>
          )}
          
          {resource.contact_info && (
            <div className="flex items-center space-x-2">
              <span>📞</span>
              <span>{resource.contact_info}</span>
            </div>
          )}
          
          <div className="flex items-center space-x-2">
            <span>⏰</span>
            <span>{new Date(resource.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    );
  };

  const ResourcesView = () => {
    const [showForm, setShowForm] = useState(false);

    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold text-gray-800">GlobalHaven Resources</h1>
              <div className="flex space-x-2">
                <button
                  onClick={() => setShowForm(true)}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-green-700 transition duration-200"
                >
                  + Share Resource
                </button>
                <button
                  onClick={() => {
                    setToken(null);
                    setCurrentView('home');
                  }}
                  className="bg-gray-500 text-white px-4 py-2 rounded-lg font-semibold hover:bg-gray-600 transition duration-200"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
            <h3 className="font-semibold text-gray-800 mb-4">Filter Resources</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Categories</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                >
                  <option value="all">All Types</option>
                  <option value="available">Available</option>
                  <option value="needed">Needed</option>
                </select>
              </div>
            </div>
          </div>

          {/* Resources Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {resources.map(resource => (
              <ResourceCard key={resource.id} resource={resource} />
            ))}
          </div>

          {resources.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">No resources found. Be the first to share!</p>
            </div>
          )}
        </div>

        {/* Resource Form Modal */}
        {showForm && (
          <ResourceForm
            onClose={() => setShowForm(false)}
            onSubmit={loadResources}
          />
        )}
      </div>
    );
  };

  const HomeView = () => (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-800 mb-6">
            Global<span className="text-green-600">Haven</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Connecting communities worldwide to share essential resources: water, food, shelter, safety, health, and economic opportunities.
          </p>
          <button
            onClick={() => setCurrentView('login')}
            className="bg-green-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-green-700 transition duration-200 shadow-lg"
          >
            Join the Community
          </button>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-16">
          {[
            { icon: '💧', title: 'Water Access', desc: 'Find safe water sources and conservation tools' },
            { icon: '🍎', title: 'Food Security', desc: 'Share excess food and find nutritious meals' },
            { icon: '🏠', title: 'Shelter Solutions', desc: 'Connect for housing and building resources' },
            { icon: '🛡️', title: 'Safety Network', desc: 'Community alerts and emergency coordination' },
            { icon: '🏥', title: 'Health Access', desc: 'Healthcare resources and wellness support' },
            { icon: '💼', title: 'Economic Empowerment', desc: 'Skills sharing and financial opportunities' }
          ].map((feature, index) => (
            <div key={index} className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-200">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold text-gray-800 mb-3">{feature.title}</h3>
              <p className="text-gray-600">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-green-600 py-16">
        <div className="max-w-4xl mx-auto text-center px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Together, we can address humanity's essential needs
          </h2>
          <p className="text-xl text-green-100 mb-8">
            Join a global community working towards universal access to water, food, shelter, safety, health, and economic security.
          </p>
          <button
            onClick={() => setCurrentView('login')}
            className="bg-white text-green-600 px-8 py-4 rounded-xl text-lg font-semibold hover:bg-gray-100 transition duration-200 shadow-lg"
          >
            Get Started Now
          </button>
        </div>
      </div>
    </div>
  );

  // Navigation logic
  if (!token && currentView !== 'home') {
    if (currentView === 'login') {
      return <LoginForm />;
    }
    return <HomeView />;
  }

  if (token) {
    return <ResourcesView />;
  }

  return <HomeView />;
}

export default App;
