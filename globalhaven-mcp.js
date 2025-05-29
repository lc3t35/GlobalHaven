#!/usr/bin/env node

const https = require('https');

class GlobalHavenMCP {
  constructor() {
    this.baseUrl =
      'https://35f32e7d-5490-42ba-9e10-affcd9163446.preview.emergentagent.com/api';
    this.apiKey = 'mcp-globalhaven-2025';
  }

  async makeRequest(endpoint, data = {}) {
    return new Promise((resolve, reject) => {
      const postData = JSON.stringify(data);
      const options = {
        hostname:
          '35f32e7d-5490-42ba-9e10-affcd9163446.preview.emergentagent.com',
        port: 443,
        path: `/api/${endpoint}`,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiKey}`,
          'Content-Length': Buffer.byteLength(postData),
        },
      };

      const req = https.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => (body += chunk));
        res.on('end', () => {
          try {
            resolve(JSON.parse(body));
          } catch (e) {
            reject(e);
          }
        });
      });

      req.on('error', reject);
      req.write(postData);
      req.end();
    });
  }

  sendResponse(id, result) {
    const response = {
      jsonrpc: '2.0',
      id: id,
      result: result,
    };
    console.log(JSON.stringify(response));
  }

  sendError(id, error) {
    const response = {
      jsonrpc: '2.0',
      id: id,
      error: {
        code: -1,
        message: error.message,
      },
    };
    console.log(JSON.stringify(response));
  }

  async handleRequest(request) {
    try {
      switch (request.method) {
        case 'initialize':
          this.sendResponse(request.id, {
            protocolVersion: '2024-11-05',
            capabilities: {
              tools: {},
            },
            serverInfo: {
              name: 'globalhaven',
              version: '1.0.0',
            },
          });
          break;

        case 'tools/list':
          this.sendResponse(request.id, {
            tools: [
              {
                name: 'search_resources',
                description:
                  'Search for community resources by category, type, and location',
                inputSchema: {
                  type: 'object',
                  properties: {
                    category: {
                      type: 'string',
                      enum: [
                        'food',
                        'water',
                        'tools',
                        'skills',
                        'shelter',
                        'medical',
                        'other',
                      ],
                      description: 'Resource category to search for',
                    },
                    type: {
                      type: 'string',
                      enum: ['available', 'needed'],
                      description:
                        'Type of resource (available to give or needed)',
                    },
                    lat: {
                      type: 'number',
                      description: 'Latitude for location-based search',
                    },
                    lng: {
                      type: 'number',
                      description: 'Longitude for location-based search',
                    },
                    radius: {
                      type: 'number',
                      default: 10,
                      description: 'Search radius in kilometers',
                    },
                  },
                },
              },
              {
                name: 'get_community_stats',
                description: 'Get community statistics and resource counts',
                inputSchema: {
                  type: 'object',
                  properties: {},
                },
              },
            ],
          });
          break;

        case 'tools/call':
          const { name, arguments: args } = request.params;

          switch (name) {
            case 'search_resources':
              const searchResult = await this.makeRequest(
                'mcp/search_resources',
                {
                  action: 'search_resources',
                  data: args,
                }
              );

              const resources = searchResult.resources || [];
              const resourceCount = resources.length;
              let resultText = `Found ${resourceCount} resources:\n\n`;

              if (searchResult.resources && searchResult.resources.length > 0) {
                searchResult.resources.forEach((resource, index) => {
                  resultText += `${index + 1}. **${resource.title}** (${
                    resource.category
                  })\n`;
                  resultText += `   Type: ${resource.type}\n`;
                  resultText += `   Description: ${resource.description}\n`;
                  if (resource.address) {
                    resultText += `   Location: ${resource.address}\n`;
                  }
                  if (resource.quantity) {
                    resultText += `   Quantity: ${resource.quantity}\n`;
                  }
                  if (resource.contact_info) {
                    resultText += `   Contact: ${resource.contact_info}\n`;
                  }
                  resultText += `   Posted: ${new Date(
                    resource.created_at
                  ).toLocaleDateString()}\n\n`;
                });
              } else {
                resultText += 'No resources found matching your criteria.';
              }

              this.sendResponse(request.id, {
                content: [
                  {
                    type: 'text',
                    text: resultText,
                  },
                ],
              });
              break;

            case 'get_community_stats':
              const statsResult = await this.makeRequest('mcp/get_user_stats', {
                action: 'get_stats',
              });

              const stats = statsResult.stats;
              let statsText = '📊 **GlobalHaven Community Statistics**\n\n';
              statsText += `👥 Total Users: ${stats.total_users}\n`;
              statsText += `📦 Total Resources: ${stats.total_resources}\n`;
              statsText += `✅ Available Resources: ${stats.available_resources}\n`;
              statsText += `🔍 Needed Resources: ${stats.needed_resources}\n\n`;
              statsText += '**Resources by Category:**\n';

              Object.entries(stats.categories).forEach(([category, count]) => {
                const emoji =
                  {
                    food: '🍎',
                    water: '💧',
                    tools: '🔧',
                    skills: '💡',
                    shelter: '🏠',
                    medical: '🏥',
                    other: '📦',
                  }[category] || '📦';
                statsText += `${emoji} ${
                  category.charAt(0).toUpperCase() + category.slice(1)
                }: ${count}\n`;
              });

              this.sendResponse(request.id, {
                content: [
                  {
                    type: 'text',
                    text: statsText,
                  },
                ],
              });
              break;

            default:
              throw new Error(`Unknown tool: ${name}`);
          }
          break;

        case 'resources/list':
          this.sendResponse(request.id, {
            resources: [],
          });
          break;

        case 'prompts/list':
          this.sendResponse(request.id, {
            prompts: [],
          });
          break;

        default:
          throw new Error(`Unknown method: ${request.method}`);
      }
    } catch (error) {
      this.sendError(request.id, error);
    }
  }
}

// Main execution
const server = new GlobalHavenMCP();

// Handle input from Claude Desktop
let inputBuffer = '';
process.stdin.on('data', (chunk) => {
  inputBuffer += chunk.toString();

  // Process complete JSON messages
  const lines = inputBuffer.split('\n');
  inputBuffer = lines.pop(); // Keep incomplete line in buffer

  for (const line of lines) {
    if (line.trim()) {
      try {
        const request = JSON.parse(line.trim());
        server.handleRequest(request);
      } catch (error) {
        // Ignore JSON parse errors for incomplete messages
      }
    }
  }
});

process.stdin.on('end', () => {
  process.exit(0);
});
