#!/bin/bash

# Cleanup Script for AutoApply Bot
# This script removes temporary files, test files, and old code

echo "🧹 Starting AutoApply Bot Cleanup..."

# Create backup directory
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup in $BACKUP_DIR..."

# Backup old app.py before deletion
if [ -f "frontend/app.py" ]; then
    cp "frontend/app.py" "$BACKUP_DIR/"
    echo "✅ Backed up old app.py"
fi

# List of files to delete
echo "🗑️  Removing temporary and test files..."

# Scripts directory cleanup
rm -f scripts/check_database_constraints.py
rm -f scripts/check_database_issues.py
rm -f scripts/check_database_schema.py
rm -f scripts/check_database_tables.py
rm -f scripts/check_environment.py
rm -f scripts/check_table_structure.py
rm -f scripts/check_user_creation.py
rm -f scripts/create_user_profile.py
rm -f scripts/create_user_profile_admin.py
rm -f scripts/debug_profile_issue.py
rm -f scripts/debug_supabase_auth.py
rm -f scripts/debug_supabase_registration.py
rm -f scripts/fix_database_constraints.py
rm -f scripts/fix_user_profiles_table.py
rm -f scripts/setup_auto_profile_creation.py
rm -f scripts/setup_auto_profiles.py
rm -f scripts/setup_supabase_database.py
rm -f scripts/setup_supabase_integration.py
rm -f scripts/setup_user_profiles.py
rm -f scripts/setup_user_profiles_rls.py
rm -f scripts/test_auth_integration.py
rm -f scripts/test_authenticated_profile.py
rm -f scripts/test_auto_profile_system.py
rm -f scripts/test_frontend_registration.py
rm -f scripts/test_frontend_templates.py
rm -f scripts/test_profile_functionality.py
rm -f scripts/test_profile_integration.py
rm -f scripts/test_supabase_auth.py
rm -f scripts/test_supabase_connection.py

echo "✅ Removed 29 temporary script files"

# Test files cleanup
rm -f tests/test_supabase_auth.py
rm -f tests/test_supabase_integration.py
rm -f tests/test_user_profiles_integration.py

echo "✅ Removed 3 redundant test files"

# Old auth files cleanup
rm -f frontend/app.py
echo "✅ Removed old app.py (superseded by app_supabase.py)"

# Temporary template files
rm -f frontend/templates/auth/test_supabase.html
echo "✅ Removed temporary test template"

# Remove empty directories
find . -type d -empty -delete
echo "✅ Removed empty directories"

echo ""
echo "🎉 Cleanup completed!"
echo "📦 Backup created in: $BACKUP_DIR"
echo ""
echo "📋 Summary:"
echo "   - Removed 29 temporary script files"
echo "   - Removed 3 redundant test files" 
echo "   - Removed old app.py"
echo "   - Removed 1 temporary template"
echo "   - Updated .gitignore"
echo ""
echo "⚠️  Next steps:"
echo "   1. Review the backup directory if needed"
echo "   2. Test the application to ensure it still works"
echo "   3. Remove console.log statements from templates"
echo "   4. Address TODO comments in code" 