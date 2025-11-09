/**
 * Setup Verification Script
 * Run with: node verify-setup.js
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Junmai AutoDev Mobile Web Setup...\n');

const checks = {
  passed: 0,
  failed: 0,
  warnings: 0
};

function checkFile(filePath, description) {
  const fullPath = path.join(__dirname, filePath);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ ${description}`);
    checks.passed++;
    return true;
  } else {
    console.log(`❌ ${description} - MISSING: ${filePath}`);
    checks.failed++;
    return false;
  }
}

function checkDirectory(dirPath, description) {
  const fullPath = path.join(__dirname, dirPath);
  if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
    console.log(`✅ ${description}`);
    checks.passed++;
    return true;
  } else {
    console.log(`❌ ${description} - MISSING: ${dirPath}`);
    checks.failed++;
    return false;
  }
}

function checkPackageJson() {
  try {
    const pkg = require('./package.json');
    const requiredDeps = ['react', 'react-dom', 'react-router-dom', 'react-scripts'];
    const requiredDevDeps = ['tailwindcss', 'autoprefixer', 'postcss'];
    
    let allPresent = true;
    
    requiredDeps.forEach(dep => {
      if (!pkg.dependencies[dep]) {
        console.log(`❌ Missing dependency: ${dep}`);
        checks.failed++;
        allPresent = false;
      }
    });
    
    requiredDevDeps.forEach(dep => {
      if (!pkg.devDependencies[dep]) {
        console.log(`❌ Missing dev dependency: ${dep}`);
        checks.failed++;
        allPresent = false;
      }
    });
    
    if (allPresent) {
      console.log(`✅ All required dependencies present`);
      checks.passed++;
    }
    
    return allPresent;
  } catch (error) {
    console.log(`❌ Error reading package.json: ${error.message}`);
    checks.failed++;
    return false;
  }
}

console.log('📦 Configuration Files:');
checkFile('package.json', 'package.json');
checkFile('tailwind.config.js', 'Tailwind configuration');
checkFile('postcss.config.js', 'PostCSS configuration');
checkFile('.env', 'Environment variables');
checkFile('.gitignore', 'Git ignore file');

console.log('\n📁 Directory Structure:');
checkDirectory('public', 'Public directory');
checkDirectory('src', 'Source directory');
checkDirectory('src/components', 'Components directory');
checkDirectory('src/pages', 'Pages directory');

console.log('\n🌐 Public Files:');
checkFile('public/index.html', 'HTML template');
checkFile('public/manifest.json', 'PWA manifest');
checkFile('public/robots.txt', 'Robots.txt');

console.log('\n⚛️ React Files:');
checkFile('src/index.js', 'Entry point');
checkFile('src/index.css', 'Global styles');
checkFile('src/App.js', 'Main app component');
checkFile('src/App.css', 'App styles');

console.log('\n🔧 Components:');
checkFile('src/components/Layout.js', 'Layout component');
checkFile('src/components/Navigation.js', 'Navigation component');

console.log('\n📄 Pages:');
checkFile('src/pages/Dashboard.js', 'Dashboard page');
checkFile('src/pages/ApprovalQueue.js', 'Approval queue page');
checkFile('src/pages/Sessions.js', 'Sessions page');
checkFile('src/pages/Settings.js', 'Settings page');
checkFile('src/pages/NotFound.js', '404 page');

console.log('\n🔔 PWA Files:');
checkFile('src/service-worker.js', 'Service worker');
checkFile('src/serviceWorkerRegistration.js', 'SW registration');
checkFile('src/reportWebVitals.js', 'Web vitals');

console.log('\n📚 Documentation:');
checkFile('README.md', 'README');
checkFile('SETUP.md', 'Setup guide');
checkFile('QUICK_START.md', 'Quick start guide');
checkFile('ARCHITECTURE.md', 'Architecture documentation');
checkFile('TASK_32_COMPLETION_SUMMARY.md', 'Task completion summary');
checkFile('NEXT_TASKS_CHECKLIST.md', 'Next tasks checklist');

console.log('\n📦 Dependencies:');
checkPackageJson();

console.log('\n' + '='.repeat(60));
console.log('📊 Verification Summary:');
console.log('='.repeat(60));
console.log(`✅ Passed: ${checks.passed}`);
console.log(`❌ Failed: ${checks.failed}`);
console.log(`⚠️  Warnings: ${checks.warnings}`);

if (checks.failed === 0) {
  console.log('\n🎉 Setup verification PASSED! Ready to install dependencies.');
  console.log('\n📝 Next steps:');
  console.log('   1. Run: npm install');
  console.log('   2. Run: npm start');
  console.log('   3. Open: http://localhost:3000');
  process.exit(0);
} else {
  console.log('\n❌ Setup verification FAILED. Please check missing files.');
  process.exit(1);
}
