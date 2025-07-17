#!/usr/bin/env node
/**
 * Health Check for Mnemosyne MCP Server
 *
 * Comprehensive system health check utility
 */

import { spawn } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import chalk from 'chalk';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');

class HealthChecker {
  constructor() {
    this.pythonPath = null;
    this.results = {
      python: { status: 'unknown', details: null },
      packages: { status: 'unknown', details: [] },
      server: { status: 'unknown', details: null },
      grpc: { status: 'unknown', details: null }
    };
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString().slice(11, 19);
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
      case 'section':
        console.log(`\\n${chalk.blue('🔍')} ${chalk.bold(message)}`);
        break;
    }
  }

  async findPython() {
    const candidates = ['python3', 'python', 'py'];

    for (const cmd of candidates) {
      try {
        const version = await this.execCommand(cmd, ['--version']);
        const match = version.match(/Python (\\d+)\\.(\\d+)\\.(\\d+)/);

        if (match) {
          const [, major, minor] = match;
          if (parseInt(major) === 3 && parseInt(minor) >= 9) {
            this.pythonPath = cmd;
            return { version, path: cmd };
          }
        }
      } catch (error) {
        continue;
      }
    }
    return null;
  }

  async checkPython() {
    this.log('Checking Python installation...', 'section');

    const pythonInfo = await this.findPython();

    if (pythonInfo) {
      this.results.python = {
        status: 'ok',
        details: pythonInfo
      };
      this.log(`Python found: ${pythonInfo.version} at ${pythonInfo.path}`, 'success');
    } else {
      this.results.python = {
        status: 'error',
        details: 'Python 3.9+ not found'
      };
      this.log('Python 3.9+ not found', 'error');
      this.log('Install from: https://python.org/downloads/', 'info');
    }

    return pythonInfo !== null;
  }

  async checkPythonPackages() {
    this.log('Checking Python packages...', 'section');

    if (!this.pythonPath) {
      this.results.packages = {
        status: 'error',
        details: 'Python not available'
      };
      return false;
    }

    const requiredPackages = [
      'fastmcp',
      'pydantic',
      'grpcio',
      'structlog'
    ];

    const packageResults = [];
    let allAvailable = true;

    for (const pkg of requiredPackages) {
      try {
        await this.execCommand(this.pythonPath, ['-c', `import ${pkg}`]);
        this.log(`${pkg}: available`, 'success');
        packageResults.push({ name: pkg, available: true });
      } catch (error) {
        this.log(`${pkg}: missing`, 'warning');
        packageResults.push({ name: pkg, available: false });
        allAvailable = false;
      }
    }

    this.results.packages = {
      status: allAvailable ? 'ok' : 'warning',
      details: packageResults
    };

    if (!allAvailable) {
      const missing = packageResults.filter(p => !p.available).map(p => p.name);
      this.log(`Install missing packages:`, 'info');
      this.log(`  Recommended: ${this.pythonPath} -m pip install -e . (from project root)`, 'info');
      this.log(`  Alternative: ${this.pythonPath} -m pip install ${missing.join(' ')}`, 'info');
    }

    return allAvailable;
  }

  async checkServerFiles() {
    this.log('Checking server files...', 'section');

    const requiredFiles = [
      { path: join(projectRoot, 'index.js'), name: 'Node.js launcher' },
      { path: join(projectRoot, 'package.json'), name: 'Package configuration' },
      { path: join(projectRoot, 'python', 'mcp_server.py'), name: 'Python server entry' }
    ];

    let allPresent = true;
    const fileResults = [];

    for (const file of requiredFiles) {
      const exists = fs.existsSync(file.path);
      fileResults.push({
        name: file.name,
        path: file.path,
        exists
      });

      if (exists) {
        this.log(`${file.name}: found`, 'success');
      } else {
        this.log(`${file.name}: missing`, 'error');
        allPresent = false;
      }
    }

    this.results.server = {
      status: allPresent ? 'ok' : 'error',
      details: fileResults
    };

    return allPresent;
  }

  async checkGrpcBackend() {
    this.log('Checking gRPC backend connectivity...', 'section');

    const grpcUrl = process.env.GRPC_BACKEND_URL || 'localhost:50051';

    try {
      // 嘗試連接到 gRPC 後端
      // 這裡我們使用一個簡單的 TCP 連接測試
      const [host, port] = grpcUrl.split(':');
      const isReachable = await this.testTcpConnection(host, parseInt(port) || 50051);

      if (isReachable) {
        this.results.grpc = {
          status: 'ok',
          details: { url: grpcUrl, reachable: true }
        };
        this.log(`gRPC backend reachable at ${grpcUrl}`, 'success');
      } else {
        this.results.grpc = {
          status: 'warning',
          details: { url: grpcUrl, reachable: false }
        };
        this.log(`gRPC backend not reachable at ${grpcUrl}`, 'warning');
        this.log('This is normal if the Mnemosyne backend is not running', 'info');
      }

      return true;
    } catch (error) {
      this.results.grpc = {
        status: 'warning',
        details: { url: grpcUrl, error: error.message }
      };
      this.log(`gRPC check failed: ${error.message}`, 'warning');
      return false;
    }
  }

  async testTcpConnection(host, port, timeout = 2000) {
    return new Promise(async (resolve) => {
      const { createConnection } = await import('net');
      const socket = createConnection({ host, port });

      const timer = setTimeout(() => {
        socket.destroy();
        resolve(false);
      }, timeout);

      socket.on('connect', () => {
        clearTimeout(timer);
        socket.destroy();
        resolve(true);
      });

      socket.on('error', () => {
        clearTimeout(timer);
        resolve(false);
      });
    });
  }

  async checkEnvironment() {
    this.log('Checking environment...', 'section');

    const env = {
      NODE_VERSION: process.version,
      PLATFORM: process.platform,
      ARCH: process.arch,
      GRPC_BACKEND_URL: process.env.GRPC_BACKEND_URL || 'localhost:50051',
      DEBUG: process.env.DEBUG || 'false'
    };

    for (const [key, value] of Object.entries(env)) {
      this.log(`${key}: ${value}`, 'info');
    }

    return true;
  }

  generateReport() {
    this.log('Health Check Report', 'section');

    const statusIcon = (status) => {
      switch (status) {
        case 'ok': return chalk.green('✅');
        case 'warning': return chalk.yellow('⚠️');
        case 'error': return chalk.red('❌');
        default: return chalk.gray('❓');
      }
    };

    console.log('\\n┌─ Component Status ─────────────────────────────┐');
    console.log(`│ Python Environment  ${statusIcon(this.results.python.status)}                       │`);
    console.log(`│ Python Packages     ${statusIcon(this.results.packages.status)}                       │`);
    console.log(`│ Server Files        ${statusIcon(this.results.server.status)}                       │`);
    console.log(`│ gRPC Backend        ${statusIcon(this.results.grpc.status)}                       │`);
    console.log('└───────────────────────────────────────────────┘\\n');

    // 整體狀態
    const allOk = Object.values(this.results).every(r => r.status === 'ok');
    const hasErrors = Object.values(this.results).some(r => r.status === 'error');

    if (allOk) {
      this.log('All systems ready! 🚀', 'success');
      this.log('Run: mnemosyne-mcp-server', 'info');
    } else if (hasErrors) {
      this.log('Critical issues found - server may not start', 'error');
    } else {
      this.log('Some warnings detected - server should work with limitations', 'warning');
    }

    return !hasErrors;
  }

  async execCommand(command, args, timeout = 5000) {
    return new Promise((resolve, reject) => {
      const child = spawn(command, args, {
        stdio: ['ignore', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      const timer = setTimeout(() => {
        child.kill();
        reject(new Error('Command timeout'));
      }, timeout);

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        clearTimeout(timer);
        if (code === 0) {
          resolve(stdout.trim());
        } else {
          reject(new Error(stderr.trim() || `Command failed with code ${code}`));
        }
      });

      child.on('error', (error) => {
        clearTimeout(timer);
        reject(error);
      });
    });
  }

  async run() {
    try {
      console.log(chalk.blue('🏥 Mnemosyne MCP Health Check\\n'));

      // 執行所有檢查
      await this.checkEnvironment();
      await this.checkPython();
      await this.checkPythonPackages();
      await this.checkServerFiles();
      await this.checkGrpcBackend();

      // 生成報告
      const success = this.generateReport();

      process.exit(success ? 0 : 1);

    } catch (error) {
      this.log(`Health check failed: ${error.message}`, 'error');
      process.exit(1);
    }
  }
}

// 主程式入口
if (import.meta.url === `file://${process.argv[1]}`) {
  const checker = new HealthChecker();
  checker.run().catch(console.error);
}

export default HealthChecker;
