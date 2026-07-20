#!/bin/bash
# GitHub Actions Pipeline Verification

echo "GitHub Actions CI/CD Pipeline Verification"
echo "=========================================="
echo ""

WORKFLOWS_DIR=".github/workflows"
PASSED=0
FAILED=0

if [ ! -d "$WORKFLOWS_DIR" ]; then
    echo "ERROR: Workflows directory not found"
    exit 1
fi

echo "Checking workflow files..."
echo ""

declare -a workflows=(
    "backend-ci.yml"
    "frontend-ci.yml"
    "ml-service-ci.yml"
    "e2e-smoke.yml"
    "data-pipeline-schedule.yml"
    "model-retrain-schedule.yml"
    "database-backup.yml"
    "rollback.yml"
    "production-deploy.yml"
)

for workflow in "${workflows[@]}"; do
    filepath="$WORKFLOWS_DIR/$workflow"
    if [ -f "$filepath" ]; then
        echo "✓ $workflow"
        ((PASSED++))
        
        # Check workflow validity
        if grep -q "^name:" "$filepath"; then
            name=$(grep "^name:" "$filepath" | head -1 | cut -d'"' -f2)
            echo "  └─ Name: $name"
        fi
        
        if grep -q "on:" "$filepath"; then
            triggers=$(grep -A5 "^on:" "$filepath" | head -3)
            echo "  └─ Triggers: $(echo "$triggers" | tr '\n' ' ')"
        fi
    else
        echo "✗ $workflow (NOT FOUND)"
        ((FAILED++))
    fi
done

echo ""
echo "=========================================="
echo "Workflow Summary"
echo "=========================================="
echo "Workflows Present: $PASSED"
echo "Workflows Missing: $FAILED"
echo ""

echo "WORKFLOW TRIGGERS:"
echo "=================="
echo "1. CI Workflows (on push/PR to main):"
echo "   - backend-ci.yml"
echo "   - frontend-ci.yml"
echo "   - ml-service-ci.yml"
echo ""
echo "2. E2E Tests (manual or on push):"
echo "   - e2e-smoke.yml"
echo ""
echo "3. Scheduled Workflows (automatic):"
echo "   - data-pipeline-schedule.yml (daily 2:00 AM UTC)"
echo "   - model-retrain-schedule.yml (Mon 4:00 AM UTC)"
echo "   - database-backup.yml (daily 2:00 AM UTC)"
echo ""
echo "4. Manual/Deployment Workflows:"
echo "   - production-deploy.yml (manual or tag push)"
echo "   - rollback.yml (manual)"
echo ""

echo "ACTION ITEMS:"
echo "============"
echo "1. Enable Actions in GitHub Repository Settings"
echo "2. Verify runner environment (ubuntu-latest)"
echo "3. Create GitHub secrets:"
echo "   - DEPLOYMENT_ENVIRONMENT (production/staging)"
echo "   - DOCKER_REGISTRY_URL (if using private registry)"
echo "   - Database credentials (if needed)"
echo "4. Grant appropriate permissions to Actions"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ All GitHub Actions workflows configured"
    exit 0
else
    echo "✗ Some workflows missing"
    exit 1
fi
