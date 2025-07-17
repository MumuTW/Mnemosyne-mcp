#!/usr/bin/env node
/**
 * Python Environment Checker for Mnemosyne MCP
 *
 * This utility checks Python installation and dependencies
 */

import { spawn } from 'child_process';
import chalk from 'chalk';

class PythonChecker {
  constructor() {
    this.pythonPath = null;
    this.verbose = process.argv.includes('--verbose');
  }

  log(message, type = 'info') {
    const prefix = chalk.cyan('[python-check]');

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
    const candidates = [
      'python3',
      'python',
      'py',
      '/usr/bin/python3',
      '/usr/local/bin/python3'
    ];

    this.log('Searching for Python interpreter...');

    for (const cmd of candidates) {
      try {
        const version = await this.execCommand(cmd, ['--version']);
        this.log(`Testing ${cmd}: ${version}`, 'debug');

        const match = version.match(/Python (\\d+)\\.(\\d+)\\.(\\d+)/);
        if (match) {
          const [, major, minor, patch] = match;
          const majorNum = parseInt(major);
          const minorNum = parseInt(minor);
          const patchNum = parseInt(patch);

          if (majorNum === 3 && minorNum >= 9) {
            this.pythonPath = cmd;
            this.log(`Found compatible Python: ${cmd} (${version})`, 'success');
            return { version: `${major}.${minor}.${patch}`, path: cmd };
          } else {
            this.log(`${cmd} version ${version} is too old (need 3.9+)`, 'warning');
          }
        }
      } catch (error) {
        this.log(`${cmd} not available: ${error.message}`, 'debug');
      }
    }

    return null;
  }

  async checkPip() {
    if (!this.pythonPath) return false;

    try {
      const pipVersion = await this.execCommand(this.pythonPath, ['-m', 'pip', '--version']);
      this.log(`pip available: ${pipVersion}`, 'success');
      return true;
    } catch (error) {
      this.log('pip not available', 'error');
      this.log('Install pip with: python3 -m ensurepip --upgrade', 'info');
      return false;
    }
  }

  async checkPackages() {
    if (!this.pythonPath) return [];

    const requiredPackages = [
      { name: 'fastmcp', import: 'fastmcp' },
      { name: 'pydantic', import: 'pydantic' },
      { name: 'grpcio', import: 'grpc' },
      { name: 'structlog', import: 'structlog' }
    ];

    const results = [];

    this.log('Checking Python packages...');

    for (const pkg of requiredPackages) {
      try {
        await this.execCommand(this.pythonPath, ['-c', `import ${pkg.import}; print("OK")`]);
        this.log(`${pkg.name}: available`, 'success');
        results.push({ ...pkg, available: true });
      } catch (error) {
        this.log(`${pkg.name}: missing`, 'warning');
        results.push({ ...pkg, available: false });
      }
    }

    return results;
  }

  async checkPythonPath() {
    if (!this.pythonPath) return false;

    try {
      const result = await this.execCommand(this.pythonPath, [
        '-c',
        'import sys; print("\\n".join(sys.path))'
      ]);

      this.log('Python path:', 'debug');
      result.split('\\n').forEach(path => {
        this.log(`  ${path}`, 'debug');
      });

      return true;
    } catch (error) {
      this.log(`Could not check Python path: ${error.message}`, 'error');
      return false;
    }
  }

  async checkSystemInfo() {
    if (!this.pythonPath) return null;

    try {
      const info = await this.execCommand(this.pythonPath, [
        '-c',
        `
import sys, platform, os
print(f"Platform: {platform.platform()}")
print(f"Architecture: {platform.machine()}")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
        `.trim()
      ]);

      this.log('System information:', 'debug');
      info.split('\\n').forEach(line => {
        if (line.trim()) {
          this.log(`  ${line}`, 'debug');
        }
      });

      return info;
    } catch (error) {
      this.log(`Could not get system info: ${error.message}`, 'warning');
      return null;
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

  showHelp() {
    console.log(`
${chalk.blue('Mnemosyne MCP Python Checker')}

Usage: node check-python.js [options]

Options:
  --verbose     Show detailed information
  --help        Show this help message

This tool checks your Python environment for Mnemosyne MCP compatibility.
`);
  }

  async run() {
    if (process.argv.includes('--help')) {
      this.showHelp();
      return;
    }

    try {
      console.log(chalk.blue('🔍 Checking Python environment for Mnemosyne MCP...\\n'));

      // 檢查 Python
      const pythonInfo = await this.findPython();
      if (!pythonInfo) {
        this.log('No compatible Python installation found', 'error');
        this.log('Please install Python 3.9+ from https://python.org', 'info');
        process.exit(1);
      }

      // 檢查 pip
      const pipAvailable = await this.checkPip();

      // 檢查包
      const packages = await this.checkPackages();
      const missingPackages = packages.filter(pkg => !pkg.available);

      // 系統信息
      if (this.verbose) {
        await this.checkSystemInfo();
        await this.checkPythonPath();
      }

      // 總結
      console.log('\\n' + chalk.blue('📋 Summary:'));
      this.log(`Python: ${pythonInfo.version} (${pythonInfo.path})`, 'success');
      this.log(`pip: ${pipAvailable ? 'available' : 'missing'}`, pipAvailable ? 'success' : 'warning');

      if (missingPackages.length === 0) {
        this.log('All required packages: available', 'success');
        console.log('\\n' + chalk.green('✅ Python environment is ready for Mnemosyne MCP!'));
      } else {
        this.log(`Missing packages: ${missingPackages.map(p => p.name).join(', ')}`, 'warning');
        console.log('\\n' + chalk.yellow('⚠️  Some packages are missing. Install with:'));
        console.log(chalk.gray(`   ${pythonInfo.path} -m pip install ${missingPackages.map(p => p.name).join(' ')}`));
      }

    } catch (error) {
      this.log(`Check failed: ${error.message}`, 'error');
      process.exit(1);
    }
  }
}

// 執行檢查
if (import.meta.url === `file://${process.argv[1]}`) {
  const checker = new PythonChecker();
  checker.run().catch(console.error);
}

export default PythonChecker;
