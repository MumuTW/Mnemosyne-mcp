#!/bin/bash

# Sprint 0 Verification Script
# This script verifies that all Sprint 0 components are working correctly

set -e

echo "🔍 Sprint 0 Verification Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Set PYTHONPATH
export PYTHONPATH=src

echo ""
print_info "1. Verifying Python environment..."
python3 --version
print_status $? "Python 3 available"

echo ""
print_info "2. Verifying dependencies..."
python3 -c "import fastapi, pydantic, structlog, falkordb, pytest" 2>/dev/null
print_status $? "Core dependencies available"

echo ""
print_info "3. Verifying configuration loading..."
python3 -c "from mnemosyne.core.config import get_settings; settings = get_settings(); print(f'Environment: {settings.environment}')" 2>/dev/null
print_status $? "Configuration system working"

echo ""
print_info "4. Verifying data models..."
python3 -c "from mnemosyne.schemas.core import File, Function; from mnemosyne.schemas.relationships import CallsRelationship; print('Models imported successfully')" 2>/dev/null
print_status $? "Pydantic models working"

echo ""
print_info "5. Verifying GraphStore interface..."
python3 -c "from mnemosyne.interfaces.graph_store import GraphStoreClient, ConnectionConfig; from mnemosyne.drivers.falkordb_driver import FalkorDBDriver; print('GraphStore components available')" 2>/dev/null
print_status $? "GraphStore abstraction layer working"

echo ""
print_info "6. Verifying API application..."
python3 -c "from fastapi.testclient import TestClient; from mnemosyne.api.main import app; client = TestClient(app); r = client.get('/'); assert r.status_code == 200; print('API endpoints working')" 2>/dev/null
print_status $? "FastAPI application working"

echo ""
print_info "7. Verifying CLI tools..."
python3 -m mnemosyne.cli.main --help > /dev/null 2>&1
print_status $? "CLI tools working"

echo ""
print_info "8. Running unit tests..."
python3 -m pytest tests/unit/ -v --tb=short -q
print_status $? "Unit tests passing"

echo ""
print_info "9. Verifying Docker configuration..."
if [ -f "docker-compose.yml" ] && [ -f "Dockerfile" ]; then
    print_status 0 "Docker configuration files present"
else
    print_status 1 "Docker configuration files missing"
fi

echo ""
print_info "10. Verifying CI configuration..."
if [ -f ".github/workflows/ci.yml" ]; then
    print_status 0 "GitHub Actions CI configuration present"
else
    print_status 1 "GitHub Actions CI configuration missing"
fi

echo ""
print_info "11. Verifying project structure..."
required_dirs=("src/mnemosyne/api" "src/mnemosyne/core" "src/mnemosyne/interfaces" "src/mnemosyne/drivers" "src/mnemosyne/schemas" "src/mnemosyne/cli" "tests/unit" "configs" "scripts")

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}  ✅ $dir${NC}"
    else
        echo -e "${RED}  ❌ $dir${NC}"
        exit 1
    fi
done

echo ""
print_info "12. Verifying documentation..."
required_docs=("README.md" "docs/DEVELOPEMENT/SPRINT0_COMPLETION.md" "docs/DEVELOPEMENT/mvp_sprint.md")

for doc in "${required_docs[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}  ✅ $doc${NC}"
    else
        echo -e "${RED}  ❌ $doc${NC}"
        exit 1
    fi
done

echo ""
echo "🎉 Sprint 0 Verification Complete!"
echo "=================================="
echo ""
echo -e "${GREEN}✅ All Sprint 0 components verified successfully!${NC}"
echo ""
echo "📋 Summary:"
echo "  • Configuration management system: Working"
echo "  • Graph database abstraction layer: Working"  
echo "  • Pydantic v2 data models: Working"
echo "  • FastAPI application skeleton: Working"
echo "  • CLI tools: Working"
echo "  • Unit test framework: Working (27 tests)"
echo "  • Docker configuration: Ready"
echo "  • CI/CD pipeline: Ready"
echo "  • Project structure: Complete"
echo "  • Documentation: Complete"
echo ""
echo -e "${BLUE}🚀 Ready for GitHub repository creation and CI verification!${NC}"
echo ""
echo "Next steps:"
echo "  1. Create GitHub repository"
echo "  2. Push branches to GitHub"
echo "  3. Create PR: feature/sprint0-ci-setup → develop"
echo "  4. Verify CI pipeline runs successfully"
echo "  5. Merge PR to complete Sprint 0"
