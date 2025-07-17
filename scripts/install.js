#!/usr/bin/env node
/**
 * Post-install script for Mnemosyne MCP Server
 *
 * This script runs after npm install to set up the Python environment
 * and verify that all dependencies are available.
 */

import { spawn } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import chalk from 'chalk';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');

class PostInstallSetup {
  constructor() {
    this.pythonPath = null;
    this.verbose = process.env.npm_config_verbose === 'true';
  }

  log(message, type = 'info') {
    const prefix = chalk.blue('[setup]');

    switch (type) {
      case 'info':
        console.log(`${prefix} ${message}`);
        break;
      case 'success':
        console.log(`${prefix} ${chalk.green('✅')} ${message}`);
        break;
      case 'warning':
        console.log(`${prefix} ${chalk.yellow('⚠️')} ${message}`);
        break;
      case 'error':
        console.error(`${prefix} ${chalk.red('❌')} ${message}`);
        break;
      case 'debug':
        if (this.verbose) {
          console.log(`${prefix} ${chalk.gray('[debug]')} ${message}`);
        }
        break;
    }
  }

  async findPython() {
    const candidates = ['python3', 'python', 'py'];

    for (const cmd of candidates) {
      try {
        const version = await this.execCommand(cmd, ['--version']);
        this.log(`Testing ${cmd}: ${version}`, 'debug');

        const match = version.match(/Python (\\d+)\\.(\\d+)/);
        if (match) {
          const [, major, minor] = match;
          if (parseInt(major) === 3 && parseInt(minor) >= 9) {
            this.pythonPath = cmd;
            return true;
          }
        }
      } catch (error) {
        this.log(`${cmd} not available`, 'debug');
        continue;
      }
    }
    return false;
  }

  async checkPython() {
    this.log('Checking Python installation...');

    if (!await this.findPython()) {
      this.log('Python 3.9+ not found', 'warning');
      this.log('Mnemosyne MCP requires Python 3.9 or higher', 'info');
      this.log('Please install Python before using this package:', 'info');
      this.log('  - Download from: https://python.org/downloads/', 'info');
      this.log('  - macOS: brew install python3', 'info');
      this.log('  - Ubuntu: sudo apt install python3 python3-pip', 'info');
      return false;
    }

    this.log(`Found Python: ${this.pythonPath}`, 'success');
    return true;
  }

  async createRequirements() {
    const requirementsPath = join(projectRoot, 'python', 'requirements.txt');

    // 確保 python 目錄存在
    const pythonDir = join(projectRoot, 'python');
    if (!fs.existsSync(pythonDir)) {
      fs.mkdirSync(pythonDir, { recursive: true });
      this.log('Created python directory', 'debug');
    }

    if (!fs.existsSync(requirementsPath)) {
      const requirements = `# Mnemosyne MCP Server Python Dependencies
# Core MCP framework
fastmcp>=2.0.0

# Data validation and settings
pydantic>=2.0.0
pydantic-settings>=2.0.0

# gRPC communication
grpcio>=1.50.0
grpcio-tools>=1.50.0

# Structured logging
structlog>=23.0.0

# Async event loop (Unix only)
uvloop>=0.17.0;platform_system!="Windows"

# HTTP client
httpx>=0.24.0

# Optional: faster JSON processing
orjson>=3.8.0
`;

      fs.writeFileSync(requirementsPath, requirements, 'utf8');
      this.log('Created requirements.txt', 'success');
    }

    return requirementsPath;
  }

  async setupPythonServer() {
    const serverPath = join(projectRoot, 'python', 'mcp_server.py');

    if (!fs.existsSync(serverPath)) {
      this.log('Creating Python MCP server entry point...');

      const serverCode = `#!/usr/bin/env python3
"""
Mnemosyne MCP Server Entry Point

This script serves as the main entry point for the Mnemosyne MCP server
when launched via the Node.js wrapper.
"""

import sys
import os
import asyncio
from pathlib import Path

def setup_python_path():
    """Setup Python path to include the Mnemosyne source code."""
    # 添加專案根目錄的 src 到 Python 路徑
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    src_path = project_root / "src"

    if src_path.exists():
        sys.path.insert(0, str(src_path))
        return True

    # 如果在開發環境中，src 可能在不同位置
    alt_src_path = project_root.parent / "src"
    if alt_src_path.exists():
        sys.path.insert(0, str(alt_src_path))
        return True

    return False

async def main():
    """Main entry point for the MCP server."""
    try:
        # 設置 Python 路徑
        if not setup_python_path():
            print("Error: Could not find Mnemosyne source code", file=sys.stderr)
            print("Please ensure the package is properly installed", file=sys.stderr)
            sys.exit(1)

        # 導入 Mnemosyne MCP 伺服器
        from mnemosyne.mcp_adapter.server import create_mcp_server
        from mnemosyne.core.config import get_settings

        # 獲取配置
        settings = get_settings()

        # 創建 MCP 伺服器
        server = await create_mcp_server(settings)

        # 啟動伺服器 (使用 stdio transport)
        server.run(transport="stdio")

    except ImportError as e:
        print(f"Import error: {e}", file=sys.stderr)
        print("Please ensure all Python dependencies are installed", file=sys.stderr)
        print("Run: pip install -r python/requirements.txt", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        if os.getenv('MCP_DEBUG') == 'true':
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # 設置事件循環策略 (Windows 兼容性)
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # 運行主程式
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
`;

      fs.writeFileSync(serverPath, serverCode, 'utf8');
      this.log('Created Python server entry point', 'success');
    }
  }

  async installPythonDependencies() {
    if (!this.pythonPath) {
      this.log('Skipping Python dependency installation (Python not found)', 'warning');
      return;
    }

    const requirementsPath = await this.createRequirements();

    this.log('Installing Python dependencies (this may take a moment)...');

    try {
      // 首先嘗試升級 pip
      try {
        await this.execCommand(this.pythonPath, ['-m', 'pip', 'install', '--upgrade', 'pip']);
        this.log('Updated pip', 'debug');
      } catch (error) {
        this.log('Could not upgrade pip, continuing...', 'debug');
      }

      // 安裝依賴 (使用 --user 避免權限問題)
      const installArgs = [
        '-m', 'pip', 'install',
        '-r', requirementsPath,
        '--user',
        '--quiet'
      ];

      await this.execCommand(this.pythonPath, installArgs);
      this.log('Python dependencies installed successfully', 'success');

    } catch (error) {
      // 如果 --user 失敗，嘗試不使用它
      try {
        const fallbackArgs = [
          '-m', 'pip', 'install',
          '-r', requirementsPath,
          '--quiet'
        ];

        await this.execCommand(this.pythonPath, fallbackArgs);
        this.log('Python dependencies installed successfully', 'success');

      } catch (fallbackError) {
        this.log('Failed to install Python dependencies', 'warning');
        this.log('You may need to install them manually:', 'info');
        this.log(`  ${this.pythonPath} -m pip install -r ${requirementsPath}`, 'info');

        if (this.verbose) {
          this.log(`Error details: ${fallbackError.message}`, 'debug');
        }
      }
    }
  }

  async createReadme() {
    const readmePath = join(projectRoot, 'README.md');

    if (!fs.existsSync(readmePath)) {
      const readme = `# Mnemosyne MCP Server

AI-powered code analysis and knowledge graph search via Model Context Protocol.

## Quick Start

\`\`\`bash
# Install globally
npm install -g @mnemosyne/mcp-server

# Or use with npx
npx @mnemosyne/mcp-server
\`\`\`

## Claude Desktop Configuration

Add to your \`~/.claude/claude_desktop_config.json\`:

\`\`\`json
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
\`\`\`

## Requirements

- Node.js 18+
- Python 3.9+

## Usage

\`\`\`bash
# Start the server
mnemosyne-mcp-server

# Check system health
mnemosyne-mcp-server --health-check

# Enable debug logging
mnemosyne-mcp-server --debug
\`\`\`

## Environment Variables

- \`GRPC_BACKEND_URL\`: gRPC backend URL (default: localhost:50051)
- \`DEBUG\`: Enable debug mode (true/false)

For more information, visit: https://github.com/MumuTW/mnemosyne-mcp
`;

      fs.writeFileSync(readmePath, readme, 'utf8');
      this.log('Created README.md', 'success');
    }
  }

  async execCommand(command, args) {
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, {
        stdio: ['ignore', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve(stdout.trim());
        } else {
          reject(new Error(stderr.trim() || `Command failed with code ${code}`));
        }
      });

      child.on('error', reject);
    });
  }

  async run() {
    try {
      console.log(chalk.blue('🔧 Setting up Mnemosyne MCP Server...'));

      // 檢查 Python
      const pythonAvailable = await this.checkPython();

      // 創建必要文件
      await this.createRequirements();
      await this.setupPythonServer();
      await this.createReadme();

      // 安裝 Python 依賴 (如果 Python 可用)
      if (pythonAvailable) {
        await this.installPythonDependencies();
      }

      console.log('');
      this.log('Setup complete! 🎉', 'success');

      if (pythonAvailable) {
        this.log('You can now run: npx @mnemosyne/mcp-server', 'info');
      } else {
        this.log('Please install Python 3.9+ and run setup again', 'warning');
      }

    } catch (error) {
      this.log(`Setup failed: ${error.message}`, 'error');

      if (this.verbose) {
        console.error(error.stack);
      }

      process.exit(1);
    }
  }
}

// 如果直接執行此腳本
if (import.meta.url === `file://${process.argv[1]}`) {
  const setup = new PostInstallSetup();
  setup.run().catch(console.error);
}

export default PostInstallSetup;
