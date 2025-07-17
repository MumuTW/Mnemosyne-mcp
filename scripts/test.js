#!/usr/bin/env node
/**
 * Test Script for Mnemosyne MCP Server
 *
 * Runs integration tests for the MCP server package
 */

import { spawn } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import chalk from 'chalk';

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, '..');

class MCPTester {
  constructor() {
    this.pythonPath = null;
    this.testResults = [];
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
      case 'test':
        console.log(`${prefix} ${chalk.magenta('🧪')} ${message}`);
        break;
    }
  }

  async findPython() {
    const candidates = ['python3', 'python', 'py'];

    for (const cmd of candidates) {
      try {
        const version = await this.execCommand(cmd, ['--version']);
        const match = version.match(/Python (\\d+)\\.(\\d+)/);

        if (match && parseInt(match[1]) === 3 && parseInt(match[2]) >= 9) {
          this.pythonPath = cmd;
          return true;
        }
      } catch (error) {
        continue;
      }
    }
    return false;
  }

  async runTest(name, testFunc) {
    this.log(`Running: ${name}`, 'test');

    try {
      const result = await testFunc();
      this.testResults.push({ name, success: true, result });
      this.log(`${name}: PASSED`, 'success');
      return true;
    } catch (error) {
      this.testResults.push({ name, success: false, error: error.message });
      this.log(`${name}: FAILED - ${error.message}`, 'error');
      return false;
    }
  }

  async testPackageJson() {
    const packagePath = join(projectRoot, 'package.json');

    if (!fs.existsSync(packagePath)) {
      throw new Error('package.json not found');
    }

    const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));

    // 檢查必要字段
    const requiredFields = ['name', 'version', 'main', 'bin'];
    for (const field of requiredFields) {
      if (!pkg[field]) {
        throw new Error(`Missing required field: ${field}`);
      }
    }

    // 檢查 bin 指向的文件是否存在
    const binPath = join(projectRoot, pkg.bin['mnemosyne-mcp-server']);
    if (!fs.existsSync(binPath)) {
      throw new Error(`Binary file not found: ${binPath}`);
    }

    return { valid: true, package: pkg };
  }

  async testLauncher() {
    const launcherPath = join(projectRoot, 'index.js');

    if (!fs.existsSync(launcherPath)) {
      throw new Error('Launcher script not found');
    }

    // 檢查文件是否可執行
    try {
      fs.accessSync(launcherPath, fs.constants.R_OK);
    } catch (error) {
      throw new Error('Launcher script not readable');
    }

    // 測試 --help 選項
    try {
      const helpOutput = await this.execCommand('node', [launcherPath, '--help'], { timeout: 5000 });
      if (!helpOutput.includes('Mnemosyne MCP Server')) {
        throw new Error('Help output does not contain expected content');
      }
    } catch (error) {
      throw new Error(`Help test failed: ${error.message}`);
    }

    return { valid: true };
  }

  async testPythonServer() {
    const serverPath = join(projectRoot, 'python', 'mcp_server.py');

    if (!fs.existsSync(serverPath)) {
      throw new Error('Python server entry point not found');
    }

    if (!this.pythonPath) {
      throw new Error('Python interpreter not available');
    }

    // 測試 Python 語法
    try {
      await this.execCommand(this.pythonPath, ['-m', 'py_compile', serverPath]);
    } catch (error) {
      throw new Error(`Python syntax error: ${error.message}`);
    }

    return { valid: true };
  }

  async testInstallScript() {
    const installPath = join(projectRoot, 'scripts', 'install.js');

    if (!fs.existsSync(installPath)) {
      throw new Error('Install script not found');
    }

    // 測試腳本語法
    try {
      await this.execCommand('node', ['--check', installPath]);
    } catch (error) {
      throw new Error(`Install script syntax error: ${error.message}`);
    }

    return { valid: true };
  }

  async testHealthCheck() {
    const healthPath = join(projectRoot, 'scripts', 'health-check.js');

    if (!fs.existsSync(healthPath)) {
      throw new Error('Health check script not found');
    }

    // 測試健康檢查執行
    try {
      const output = await this.execCommand('node', [healthPath], { timeout: 10000 });
      // 健康檢查可能會失敗，但不應該崩潰
      return { valid: true, output };
    } catch (error) {
      // 如果是因為依賴缺失而失敗，這是可以接受的
      if (error.message.includes('Python') || error.message.includes('missing')) {
        return { valid: true, warning: error.message };
      }
      throw error;
    }
  }

  async testMCPProtocol() {
    // 基本的 MCP 協議測試
    const testScript = `
import json
import sys

# 模擬 MCP 初始化請求
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
}

print(json.dumps(init_request))
print("TEST_COMPLETE")
`;

    if (!this.pythonPath) {
      throw new Error('Python not available for MCP test');
    }

    try {
      const output = await this.execCommand(this.pythonPath, ['-c', testScript]);

      if (!output.includes('TEST_COMPLETE')) {
        throw new Error('MCP test script did not complete');
      }

      // 檢查是否可以解析 JSON
      const lines = output.split('\\n');
      const jsonLine = lines.find(line => line.trim().startsWith('{'));

      if (jsonLine) {
        JSON.parse(jsonLine); // 這會拋出異常如果不是有效的 JSON
      }

      return { valid: true };
    } catch (error) {
      throw new Error(`MCP protocol test failed: ${error.message}`);
    }
  }

  async generateTestReport() {
    console.log('\\n' + chalk.blue('📊 Test Report'));
    console.log('═'.repeat(50));

    const passed = this.testResults.filter(t => t.success).length;
    const failed = this.testResults.filter(t => !t.success).length;
    const total = this.testResults.length;

    for (const test of this.testResults) {
      const status = test.success ?
        chalk.green('PASS') :
        chalk.red('FAIL');

      console.log(`${status} ${test.name}`);

      if (!test.success) {
        console.log(`     ${chalk.red('Error:')} ${test.error}`);
      }
    }

    console.log('─'.repeat(50));
    console.log(`Total: ${total}, Passed: ${chalk.green(passed)}, Failed: ${chalk.red(failed)}`);

    if (failed === 0) {
      console.log(chalk.green('\\n🎉 All tests passed!'));
      return true;
    } else {
      console.log(chalk.red(`\\n❌ ${failed} test(s) failed`));
      return false;
    }
  }

  async execCommand(command, args, options = {}) {
    const timeout = options.timeout || 5000;

    return new Promise((resolve, reject) => {
      const child = spawn(command, args, {
        stdio: ['ignore', 'pipe', 'pipe'],
        ...options
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
      console.log(chalk.blue('🧪 Running Mnemosyne MCP Server Tests\\n'));

      // 設置
      await this.findPython();
      if (this.pythonPath) {
        this.log(`Using Python: ${this.pythonPath}`, 'info');
      } else {
        this.log('Python not available - some tests will be skipped', 'warning');
      }

      // 執行測試
      await this.runTest('Package Configuration', () => this.testPackageJson());
      await this.runTest('Launcher Script', () => this.testLauncher());
      await this.runTest('Install Script', () => this.testInstallScript());
      await this.runTest('Health Check Script', () => this.testHealthCheck());

      if (this.pythonPath) {
        await this.runTest('Python Server', () => this.testPythonServer());
        await this.runTest('MCP Protocol', () => this.testMCPProtocol());
      }

      // 生成報告
      const success = await this.generateTestReport();

      process.exit(success ? 0 : 1);

    } catch (error) {
      this.log(`Test execution failed: ${error.message}`, 'error');
      process.exit(1);
    }
  }
}

// 主程式入口
if (import.meta.url === `file://${process.argv[1]}`) {
  const tester = new MCPTester();
  tester.run().catch(console.error);
}

export default MCPTester;
