# @mnemosyne/mcp-server

[![npm version](https://badge.fury.io/js/@mnemosyne%2Fmcp-server.svg)](https://badge.fury.io/js/@mnemosyne%2Fmcp-server)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen.svg)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/python-%3E%3D3.9-blue.svg)](https://python.org/)

AI-powered code analysis and knowledge graph search via Model Context Protocol (MCP).

Mnemosyne MCP Server provides intelligent code search, impact analysis, and software engineering insights through a robust graph-based knowledge representation.

## ✨ Features

- 🔍 **Smart Code Search**: Semantic code search across your entire codebase
- 📊 **Impact Analysis**: Understand the ripple effects of code changes
- 🕷️ **Knowledge Graph**: Rich graph representation of code relationships
- 🤖 **AI Integration**: Seamless integration with Claude Desktop and other MCP clients
- ⚡ **High Performance**: gRPC backend with efficient graph traversal
- 🔧 **Easy Setup**: One-command installation and configuration

## 🚀 Quick Start

### Installation

```bash
# Install globally
npm install -g @mnemosyne/mcp-server

# Or use with npx (recommended)
npx @mnemosyne/mcp-server
```

### Prerequisites

- **Node.js 18+**: Download from [nodejs.org](https://nodejs.org/)
- **Python 3.9+**: Download from [python.org](https://www.python.org/downloads/)

The installer will automatically check dependencies and guide you through setup.

### Claude Desktop Configuration

Add to your `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mnemosyne": {
      "command": "npx",
      "args": ["@mnemosyne/mcp-server"],
      "env": {
        "GRPC_BACKEND_URL": "localhost:50051"
      }
    }
  }
}
```

Restart Claude Desktop after adding the configuration.

## 🔧 Usage

### Starting the Server

```bash
# Basic usage
mnemosyne-mcp-server

# With debug logging
mnemosyne-mcp-server --debug

# Check system health
mnemosyne-mcp-server --health-check

# Show help
mnemosyne-mcp-server --help
```

### Available Tools in Claude

Once configured, you'll have access to these tools in Claude:

- **Search Code**: Semantic search across your codebase
- **Analyze Impact**: Understand how changes affect your system
- **System Status**: Check backend connectivity and health
- **Get System Info**: View server configuration and statistics

### Example Usage in Claude

```
You: "Search for authentication logic in my codebase"

Claude will use the search_code tool to find relevant authentication-related code and explain what it found.

You: "What would be the impact of changing the User model?"

Claude will use the analyze_impact tool to show you all the code that depends on the User model.
```

## 🏗️ Architecture

Mnemosyne uses a hybrid Node.js/Python architecture:

- **Node.js Launcher**: Handles installation, dependency management, and process lifecycle
- **Python MCP Server**: Implements the Model Context Protocol and business logic
- **gRPC Backend**: High-performance graph operations and analysis
- **Knowledge Graph**: Rich representation of code relationships and dependencies

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRPC_BACKEND_URL` | `localhost:50051` | gRPC backend server URL |
| `DEBUG` | `false` | Enable debug logging |
| `MCP_DEBUG` | `false` | Enable MCP protocol debug logging |

### Advanced Configuration

For advanced users, you can configure the underlying Mnemosyne system by placing configuration files in your project:

- `.mnemosyne/config.yaml` - Main configuration
- `.mnemosyne/constraints.yaml` - Code governance rules

See the [Mnemosyne documentation](https://github.com/MumuTW/mnemosyne-mcp) for detailed configuration options.

## 🛠️ Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/MumuTW/mnemosyne-mcp.git
cd mnemosyne-mcp

# Install dependencies
npm install

# Run tests
npm test

# Check system health
npm run health-check
```

### Python Development

The Python components are located in the `python/` directory:

```bash
# Install Python dependencies
pip install -r python/requirements.txt

# Run the Python server directly
python python/mcp_server.py
```

## 🧪 Testing

```bash
# Run all tests
npm test

# Check Python environment
npm run check-python

# Full system health check
npm run health-check
```

## 📚 Documentation

- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP documentation
- [Claude Desktop Setup](https://claude.ai/docs) - Guide to configuring Claude Desktop
- [Mnemosyne Project](https://github.com/MumuTW/mnemosyne-mcp) - Main project repository

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

### Common Issues

**"Python 3.9+ not found"**
- Install Python from [python.org](https://python.org)
- On macOS: `brew install python3`
- On Ubuntu: `sudo apt install python3 python3-pip`

**"Failed to install Python dependencies"**
- Try: `python3 -m pip install --user -r python/requirements.txt`
- Check your internet connection
- Ensure pip is up to date: `python3 -m pip install --upgrade pip`

**"gRPC backend not reachable"**
- This is normal if you haven't started the Mnemosyne backend
- The MCP server will work with limited functionality
- See the main project for backend setup instructions

**Claude Desktop not detecting the server**
- Verify your `claude_desktop_config.json` syntax
- Restart Claude Desktop after configuration changes
- Check the Claude Desktop logs for error messages

### Getting Help

- 🐛 [Report Issues](https://github.com/MumuTW/mnemosyne-mcp/issues)
- 💬 [Discussions](https://github.com/MumuTW/mnemosyne-mcp/discussions)
- 📧 [Email Support](mailto:support@mnemosyne.dev)

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Enable all debug logging
DEBUG=true mnemosyne-mcp-server --debug

# Or set environment variable
export DEBUG=true
mnemosyne-mcp-server
```

---

<div align="center">
  <p>
    <a href="https://github.com/MumuTW/mnemosyne-mcp">🏠 Home</a> •
    <a href="https://github.com/MumuTW/mnemosyne-mcp/issues">🐛 Issues</a> •
    <a href="https://github.com/MumuTW/mnemosyne-mcp/discussions">💬 Discussions</a>
  </p>
  <p>Made with ❤️ by the Mnemosyne Team</p>
</div>
