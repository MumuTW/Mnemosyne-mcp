#!/usr/bin/env node
/**
 * Mnemosyne MCP Server Launcher
 *
 * This Node.js launcher handles Python environment setup and server execution
 * for the Mnemosyne Model Context Protocol server.
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';
import chalk from 'chalk';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class MnemosyneMCPLauncher {
  constructor() {
    this.pythonPath = null;
    this.serverPath = join(__dirname, 'python', 'mcp_server.py');
    this.debug = process.env.DEBUG === 'true' || process.argv.includes('--debug');
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString().slice(11, 23);
    const prefix = chalk.gray(`[${timestamp}]`);

    switch (type) {
      case 'info':
        console.log(`${prefix} ${chalk.blue('ℹ')} ${message}`);
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
        if (this.debug) {
          console.log(`${prefix} ${chalk.magenta('🔍')} ${chalk.dim(message)}`);
        }
        break;
    }
  }

  async findPython() {
    const candidates = [
      'python3',
      'python',
      'py',
      '/usr/bin/python3',
      '/usr/local/bin/python3',
      process.platform === 'win32' ? 'py.exe' : null
    ].filter(Boolean);

    this.log('Searching for Python interpreter...', 'debug');

    for (const cmd of candidates) {
      try {
        const version = await this.execCommand(cmd, ['--version']);
        this.log(`Testing ${cmd}: ${version}`, 'debug');

        // 檢查是否為 Python 3.9+
        const match = version.match(/Python (\\d+)\\.(\\d+)/);
        if (match) {
          const [, major, minor] = match;
          if (parseInt(major) === 3 && parseInt(minor) >= 9) {
            this.pythonPath = cmd;
            this.log(`Found compatible Python: ${cmd} (${version})`, 'success');
            return true;
          }
        }
      } catch (error) {
        this.log(`${cmd} not available: ${error.message}`, 'debug');
        continue;
      }
    }
    return false;
  }

  async checkPythonDependencies() {
    this.log('Checking Python dependencies...', 'debug');

    const requiredPackages = [
      'fastmcp',
      'pydantic',
      'grpcio',
      'structlog'
    ];

    const missingPackages = [];

    for (const pkg of requiredPackages) {
      try {
        await this.execCommand(this.pythonPath, ['-c', `import ${pkg}`]);
        this.log(`${pkg}: available`, 'debug');
      } catch (error) {
        this.log(`${pkg}: missing`, 'debug');
        missingPackages.push(pkg);
      }
    }

    if (missingPackages.length > 0) {
      this.log(`Missing Python packages: ${missingPackages.join(', ')}`, 'warning');
      return false;
    }

    this.log('All Python dependencies available', 'success');
    return true;
  }

  async installPythonDeps() {
    const requirementsPath = join(__dirname, 'python', 'requirements.txt');

    if (!fs.existsSync(requirementsPath)) {
      this.log('requirements.txt not found, creating minimal dependencies...', 'warning');
      await this.createRequirements(requirementsPath);
    }

    this.log('Installing Python dependencies...', 'info');

    try {
      const output = await this.execCommand(this.pythonPath, [
        '-m', 'pip', 'install', '-r', requirementsPath, '--user'
      ]);

      this.log('Python dependencies installed successfully', 'success');
      this.log(output, 'debug');
    } catch (error) {
      // 嘗試不使用 --user 標誌
      try {
        await this.execCommand(this.pythonPath, [
          '-m', 'pip', 'install', '-r', requirementsPath
        ]);
        this.log('Python dependencies installed successfully', 'success');
      } catch (fallbackError) {
        throw new Error(`Failed to install dependencies: ${fallbackError.message}`);
      }
    }
  }

  async createRequirements(requirementsPath) {
    const requirements = `# Mnemosyne MCP Server Requirements
fastmcp>=2.0.0
pydantic>=2.0.0
grpcio>=1.50.0
grpcio-tools>=1.50.0
structlog>=23.0.0
uvloop>=0.17.0;platform_system!="Windows"
`;

    fs.writeFileSync(requirementsPath, requirements, 'utf8');
    this.log('Created requirements.txt', 'debug');
  }

  async createPythonServer() {
    // 如果 Python 伺服器不存在，創建一個基本的
    if (!fs.existsSync(this.serverPath)) {
      this.log('Creating Python MCP server...', 'info');

      const serverCode = `#!/usr/bin/env python3
"""
Mnemosyne MCP Server Entry Point
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加專案路徑到 Python 路徑
project_root = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(project_root))

async def main():
    try:
        from mnemosyne.mcp_adapter.server import create_mcp_server
        from mnemosyne.core.config import get_settings

        # 獲取配置
        settings = get_settings()

        # 創建並啟動 MCP 伺服器
        server = await create_mcp_server(settings)

        # 啟動伺服器 (stdio transport)
        server.run()

    except ImportError as e:
        print(f"Import error: {e}", file=sys.stderr)
        print("Please ensure Mnemosyne is properly installed", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
`;

      fs.writeFileSync(this.serverPath, serverCode, 'utf8');
      this.log('Python server created', 'success');
    }
  }

  async checkDependencies() {
    this.log('Checking system dependencies...', 'info');

    // 檢查 Python
    if (!await this.findPython()) {
      this.log('Python 3.9+ is required but not found', 'error');
      this.log('Please install Python from https://python.org', 'info');
      this.log('Or using your system package manager:', 'info');
      this.log('  macOS: brew install python3', 'info');
      this.log('  Ubuntu: sudo apt install python3 python3-pip', 'info');
      this.log('  Windows: Download from python.org', 'info');
      process.exit(1);
    }

    // 檢查 Python 包
    if (!await this.checkPythonDependencies()) {
      this.log('Installing missing Python dependencies...', 'warning');
      await this.installPythonDeps();
    }

    // 確保 Python 伺服器存在
    await this.createPythonServer();
  }

  async startServer() {
    this.log('Starting Mnemosyne MCP Server...', 'info');

    const env = {
      ...process.env,
      PYTHONPATH: join(__dirname, 'src'),
      GRPC_BACKEND_URL: process.env.GRPC_BACKEND_URL || 'localhost:50051',
      MCP_DEBUG: this.debug ? 'true' : 'false'
    };

    this.log(`Python path: ${this.pythonPath}`, 'debug');
    this.log(`Server path: ${this.serverPath}`, 'debug');
    this.log(`Environment: ${JSON.stringify(env, null, 2)}`, 'debug');

    const serverProcess = spawn(this.pythonPath, [this.serverPath], {
      stdio: ['inherit', 'inherit', 'inherit'],
      env
    });

    serverProcess.on('error', (error) => {
      this.log(`Failed to start server: ${error.message}`, 'error');
      process.exit(1);
    });

    serverProcess.on('exit', (code, signal) => {
      if (signal) {
        this.log(`Server terminated by signal: ${signal}`, 'warning');
      } else if (code !== 0) {
        this.log(`Server exited with code ${code}`, 'error');
        process.exit(code);
      }
    });

    // 優雅關閉處理
    const shutdown = (signal) => {
      this.log(`Received ${signal}, shutting down server...`, 'warning');
      serverProcess.kill('SIGINT');

      setTimeout(() => {
        this.log('Force killing server process', 'warning');
        serverProcess.kill('SIGKILL');
        process.exit(1);
      }, 5000);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));
  }

  async execCommand(command, args, options = {}) {
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, {
        stdio: ['ignore', 'pipe', 'pipe'],
        ...options
      });

      let stdout = '';
      let stderr = '';

      child.stdout?.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr?.on('data', (data) => {
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

  async handleArguments() {
    const args = process.argv.slice(2);

    if (args.includes('--help') || args.includes('-h')) {
      this.showHelp();
      process.exit(0);
    }

    if (args.includes('--version') || args.includes('-v')) {
      const packageJson = JSON.parse(
        fs.readFileSync(join(__dirname, 'package.json'), 'utf8')
      );
      console.log(packageJson.version);
      process.exit(0);
    }

    if (args.includes('--health-check')) {
      await this.healthCheck();
      process.exit(0);
    }
  }

  showHelp() {
    const help = `
${chalk.blue('Mnemosyne MCP Server')}

Usage: mnemosyne-mcp-server [options]

Options:
  -h, --help           Show this help message
  -v, --version        Show version number
  --debug              Enable debug logging
  --health-check       Check system health and exit

Environment Variables:
  GRPC_BACKEND_URL     gRPC backend URL (default: localhost:50051)
  DEBUG                Enable debug mode (true/false)

Examples:
  mnemosyne-mcp-server                    # Start the server
  mnemosyne-mcp-server --debug            # Start with debug logging
  mnemosyne-mcp-server --health-check     # Check system status

For more information, visit: https://github.com/MumuTW/mnemosyne-mcp
`;
    console.log(help);
  }

  async healthCheck() {
    this.log('Running health check...', 'info');

    try {
      await this.checkDependencies();
      this.log('Health check passed - all dependencies available', 'success');
    } catch (error) {
      this.log(`Health check failed: ${error.message}`, 'error');
      process.exit(1);
    }
  }

  async run() {
    try {
      // 處理命令列參數
      await this.handleArguments();

      // 檢查依賴
      await this.checkDependencies();

      // 啟動伺服器
      await this.startServer();

    } catch (error) {
      this.log(`Failed to start Mnemosyne MCP: ${error.message}`, 'error');

      if (this.debug) {
        console.error(error.stack);
      }

      process.exit(1);
    }
  }
}

// 主程式入口
if (import.meta.url === `file://${process.argv[1]}`) {
  const launcher = new MnemosyneMCPLauncher();
  launcher.run().catch(console.error);
}

export default MnemosyneMCPLauncher;
