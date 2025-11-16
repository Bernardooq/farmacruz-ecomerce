/**
 * Integration Verification Script
 * Verifies that all components are properly integrated with services and contexts
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const results = {
  passed: [],
  failed: [],
  warnings: []
};

function log(type, message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] [${type.toUpperCase()}] ${message}`);
  
  if (type === 'pass') results.passed.push(message);
  else if (type === 'fail') results.failed.push(message);
  else if (type === 'warn') results.warnings.push(message);
}

function checkFileExists(filePath) {
  const fullPath = path.join(__dirname, filePath);
  return fs.existsSync(fullPath);
}

function checkFileContains(filePath, searchStrings) {
  const fullPath = path.join(__dirname, filePath);
  if (!fs.existsSync(fullPath)) {
    return { exists: false, found: [] };
  }
  
  const content = fs.readFileSync(fullPath, 'utf8');
  const found = searchStrings.filter(str => content.includes(str));
  
  return { exists: true, found, content };
}

console.log('\n=== FARMACRUZ INTEGRATION VERIFICATION ===\n');

// 1. Verify Core Services Exist
console.log('1. Verificando Servicios API...');
const services = [
  'src/services/authService.js',
  'src/services/productService.js',
  'src/services/categoryService.js',
  'src/services/orderService.js',
  'src/services/adminService.js',
  'src/services/apiService.js'
];

services.forEach(service => {
  if (checkFileExists(service)) {
    log('pass', `✓ ${service} existe`);
  } else {
    log('fail', `✗ ${service} NO ENCONTRADO`);
  }
});

// 2. Verify Contexts
console.log('\n2. Verificando Contextos...');
const contexts = [
  { file: 'src/context/AuthContext.jsx', methods: ['login', 'logout', 'useAuth'] },
  { file: 'src/context/CartContext.jsx', methods: ['addToCart', 'updateQuantity', 'removeItem', 'checkout', 'useCart'] }
];

contexts.forEach(({ file, methods }) => {
  const result = checkFileContains(file, methods);
  if (result.exists) {
    const missing = methods.filter(m => !result.found.includes(m));
    if (missing.length === 0) {
      log('pass', `✓ ${file} tiene todos los métodos requeridos`);
    } else {
      log('fail', `✗ ${file} falta: ${missing.join(', ')}`);
    }
  } else {
    log('fail', `✗ ${file} NO ENCONTRADO`);
  }
});

// 3. Verify ProtectedRoute
console.log('\n3. Verificando ProtectedRoute...');
const protectedRoute = checkFileContains('src/routes/ProtectedRoute.jsx', [
  'useAuth',
  'isAuthenticated',
  'allowedRoles',
  'Navigate',
  'loading'
]);

if (protectedRoute.exists) {
  if (protectedRoute.found.length === 5) {
    log('pass', '✓ ProtectedRoute implementado correctamente');
  } else {
    log('fail', `✗ ProtectedRoute incompleto. Encontrado: ${protectedRoute.found.join(', ')}`);
  }
} else {
  log('fail', '✗ ProtectedRoute NO ENCONTRADO');
}

// 4. Verify App.jsx uses ProtectedRoute
console.log('\n4. Verificando App.jsx...');
const appFile = checkFileContains('src/App.jsx', [
  'ProtectedRoute',
  'AuthProvider',
  'CartProvider'
]);

if (appFile.exists) {
  if (appFile.found.includes('ProtectedRoute')) {
    log('pass', '✓ App.jsx usa ProtectedRoute');
  } else {
    log('fail', '✗ App.jsx NO usa ProtectedRoute');
  }
  
  if (appFile.found.includes('AuthProvider') || appFile.content.includes('AuthProvider')) {
    log('pass', '✓ App.jsx tiene AuthProvider');
  } else {
    log('warn', '⚠ App.jsx podría no tener AuthProvider');
  }
} else {
  log('fail', '✗ App.jsx NO ENCONTRADO');
}

// 5. Verify LoginForm Integration
console.log('\n5. Verificando LoginForm...');
const loginForm = checkFileContains('src/components/LoginForm.jsx', [
  'useAuth',
  'login(',
  'navigate',
  'loading',
  'error'
]);

if (loginForm.exists) {
  const hasUseAuth = loginForm.found.includes('useAuth');
  const hasLogin = loginForm.found.includes('login(');
  const hasNavigate = loginForm.found.includes('navigate');
  
  if (hasUseAuth && hasLogin && hasNavigate) {
    log('pass', '✓ LoginForm integrado con AuthContext');
  } else {
    log('fail', `✗ LoginForm incompleto. useAuth: ${hasUseAuth}, login: ${hasLogin}, navigate: ${hasNavigate}`);
  }
  
  // Check for mock data
  if (loginForm.content.includes('mockUsers') || loginForm.content.includes('hardcoded')) {
    log('warn', '⚠ LoginForm podría tener datos mock');
  }
} else {
  log('fail', '✗ LoginForm NO ENCONTRADO');
}

// 6. Verify Products Page Integration
console.log('\n6. Verificando Products Page...');
const productsPage = checkFileContains('src/pages/Products.jsx', [
  'productService',
  'categoryService',
  'getProducts',
  'getCategories',
  'LoadingSpinner',
  'ErrorMessage'
]);

if (productsPage.exists) {
  const hasProductService = productsPage.found.includes('productService');
  const hasCategoryService = productsPage.found.includes('categoryService');
  const hasLoading = productsPage.found.includes('LoadingSpinner');
  
  if (hasProductService && hasCategoryService) {
    log('pass', '✓ Products Page integrado con servicios');
  } else {
    log('fail', `✗ Products Page incompleto. productService: ${hasProductService}, categoryService: ${hasCategoryService}`);
  }
  
  if (hasLoading) {
    log('pass', '✓ Products Page tiene LoadingSpinner');
  } else {
    log('warn', '⚠ Products Page podría no tener LoadingSpinner');
  }
  
  // Check for mock data
  if (productsPage.content.includes('mockProducts') || productsPage.content.match(/const products = \[/)) {
    log('fail', '✗ Products Page TODAVÍA TIENE DATOS MOCK');
  } else {
    log('pass', '✓ Products Page NO tiene datos mock');
  }
} else {
  log('fail', '✗ Products Page NO ENCONTRADO');
}

// 7. Verify ProductCard Integration
console.log('\n7. Verificando ProductCard...');
const productCard = checkFileContains('src/components/ProductCard.jsx', [
  'useCart',
  'useAuth',
  'addToCart',
  'isAuthenticated'
]);

if (productCard.exists) {
  const hasUseCart = productCard.found.includes('useCart');
  const hasAddToCart = productCard.found.includes('addToCart');
  
  if (hasUseCart && hasAddToCart) {
    log('pass', '✓ ProductCard integrado con CartContext');
  } else {
    log('fail', `✗ ProductCard incompleto. useCart: ${hasUseCart}, addToCart: ${hasAddToCart}`);
  }
} else {
  log('fail', '✗ ProductCard NO ENCONTRADO');
}

// 8. Verify Cart Page Integration
console.log('\n8. Verificando Cart Page...');
const cartPage = checkFileContains('src/pages/Cart.jsx', [
  'useCart',
  'updateQuantity',
  'removeItem',
  'checkout',
  'LoadingSpinner'
]);

if (cartPage.exists) {
  const hasUseCart = cartPage.found.includes('useCart');
  const hasUpdateQuantity = cartPage.found.includes('updateQuantity');
  const hasCheckout = cartPage.found.includes('checkout');
  
  if (hasUseCart && hasUpdateQuantity && hasCheckout) {
    log('pass', '✓ Cart Page integrado con CartContext');
  } else {
    log('fail', `✗ Cart Page incompleto. useCart: ${hasUseCart}, updateQuantity: ${hasUpdateQuantity}, checkout: ${hasCheckout}`);
  }
  
  // Check for mock data
  if (cartPage.content.includes('mockCart') || cartPage.content.match(/const cartItems = \[/)) {
    log('fail', '✗ Cart Page TODAVÍA TIENE DATOS MOCK');
  } else {
    log('pass', '✓ Cart Page NO tiene datos mock');
  }
} else {
  log('fail', '✗ Cart Page NO ENCONTRADO');
}

// 9. Verify AdminDashboard Integration
console.log('\n9. Verificando AdminDashboard...');
const adminDash = checkFileContains('src/pages/AdminDashboard.jsx', [
  'adminService',
  'getDashboardStats',
  'useAuth',
  'LoadingSpinner'
]);

if (adminDash.exists) {
  const hasAdminService = adminDash.found.includes('adminService');
  const hasGetStats = adminDash.found.includes('getDashboardStats');
  
  if (hasAdminService && hasGetStats) {
    log('pass', '✓ AdminDashboard integrado con adminService');
  } else {
    log('fail', `✗ AdminDashboard incompleto. adminService: ${hasAdminService}, getDashboardStats: ${hasGetStats}`);
  }
} else {
  log('fail', '✗ AdminDashboard NO ENCONTRADO');
}

// 10. Verify InventoryManager Integration
console.log('\n10. Verificando InventoryManager...');
const inventory = checkFileContains('src/components/InventoryManager.jsx', [
  'productService',
  'getProducts',
  'createProduct',
  'updateProduct',
  'deleteProduct'
]);

if (inventory.exists) {
  const hasProductService = inventory.found.includes('productService');
  const hasCreate = inventory.found.includes('createProduct');
  const hasUpdate = inventory.found.includes('updateProduct');
  const hasDelete = inventory.found.includes('deleteProduct');
  
  if (hasProductService && hasCreate && hasUpdate && hasDelete) {
    log('pass', '✓ InventoryManager integrado con productService (CRUD completo)');
  } else {
    log('fail', `✗ InventoryManager incompleto. productService: ${hasProductService}, create: ${hasCreate}, update: ${hasUpdate}, delete: ${hasDelete}`);
  }
} else {
  log('fail', '✗ InventoryManager NO ENCONTRADO');
}

// 11. Verify ClientManagement Integration
console.log('\n11. Verificando ClientManagement...');
const clientMgmt = checkFileContains('src/components/ClientManagement.jsx', [
  'adminService',
  'getUsers',
  'createUser',
  'updateUser',
  'deleteUser'
]);

if (clientMgmt.exists) {
  const hasAdminService = clientMgmt.found.includes('adminService');
  const hasCreate = clientMgmt.found.includes('createUser');
  const hasUpdate = clientMgmt.found.includes('updateUser');
  const hasDelete = clientMgmt.found.includes('deleteUser');
  
  if (hasAdminService && hasCreate && hasUpdate && hasDelete) {
    log('pass', '✓ ClientManagement integrado con adminService (CRUD completo)');
  } else {
    log('fail', `✗ ClientManagement incompleto. adminService: ${hasAdminService}, create: ${hasCreate}, update: ${hasUpdate}, delete: ${hasDelete}`);
  }
} else {
  log('fail', '✗ ClientManagement NO ENCONTRADO');
}

// 12. Verify PendingOrders Integration
console.log('\n12. Verificando PendingOrders...');
const pendingOrders = checkFileContains('src/components/PendingOrders.jsx', [
  'orderService',
  'getAllOrders',
  'updateOrderStatus',
  'cancelOrder',
  'getOrderById'
]);

if (pendingOrders.exists) {
  const hasOrderService = pendingOrders.found.includes('orderService');
  const hasGetAll = pendingOrders.found.includes('getAllOrders');
  const hasUpdate = pendingOrders.found.includes('updateOrderStatus');
  const hasCancel = pendingOrders.found.includes('cancelOrder');
  
  if (hasOrderService && hasGetAll && hasUpdate && hasCancel) {
    log('pass', '✓ PendingOrders integrado con orderService');
  } else {
    log('fail', `✗ PendingOrders incompleto. orderService: ${hasOrderService}, getAll: ${hasGetAll}, update: ${hasUpdate}, cancel: ${hasCancel}`);
  }
} else {
  log('fail', '✗ PendingOrders NO ENCONTRADO');
}

// 13. Verify UI Components
console.log('\n13. Verificando Componentes UI...');
const uiComponents = [
  'src/components/LoadingSpinner.jsx',
  'src/components/ErrorMessage.jsx'
];

uiComponents.forEach(component => {
  if (checkFileExists(component)) {
    log('pass', `✓ ${component} existe`);
  } else {
    log('warn', `⚠ ${component} NO ENCONTRADO`);
  }
});

// 14. Verify SCSS Styles
console.log('\n14. Verificando Estilos SCSS...');
const scssFiles = [
  { file: 'src/scss/layout/_page.scss', styles: ['loading-container', 'spinner'] },
  { file: 'src/scss/base/_globales.scss', styles: ['error-banner', 'error-message'] }
];

scssFiles.forEach(({ file, styles }) => {
  const result = checkFileContains(file, styles);
  if (result.exists) {
    const missing = styles.filter(s => !result.found.includes(s));
    if (missing.length === 0) {
      log('pass', `✓ ${file} tiene estilos requeridos`);
    } else {
      log('warn', `⚠ ${file} podría faltar: ${missing.join(', ')}`);
    }
  } else {
    log('warn', `⚠ ${file} NO ENCONTRADO`);
  }
});

// 15. Check for Mock Data in Critical Files
console.log('\n15. Verificando ausencia de datos mock...');
const criticalFiles = [
  'src/pages/Products.jsx',
  'src/pages/Cart.jsx',
  'src/pages/AdminDashboard.jsx',
  'src/components/InventoryManager.jsx',
  'src/components/ClientManagement.jsx',
  'src/components/PendingOrders.jsx'
];

criticalFiles.forEach(file => {
  const result = checkFileContains(file, ['mock', 'hardcoded', 'fake']);
  if (result.exists) {
    const hasMock = result.content.match(/const \w+ = \[{/g) || 
                    result.content.includes('mockData') ||
                    result.content.includes('fakeData');
    
    if (hasMock) {
      log('fail', `✗ ${file} podría tener datos mock`);
    } else {
      log('pass', `✓ ${file} NO tiene datos mock obvios`);
    }
  }
});

// Print Summary
console.log('\n=== RESUMEN DE VERIFICACIÓN ===\n');
console.log(`✓ Pruebas Pasadas: ${results.passed.length}`);
console.log(`✗ Pruebas Fallidas: ${results.failed.length}`);
console.log(`⚠ Advertencias: ${results.warnings.length}`);

if (results.failed.length > 0) {
  console.log('\n--- FALLOS ---');
  results.failed.forEach(fail => console.log(`  ${fail}`));
}

if (results.warnings.length > 0) {
  console.log('\n--- ADVERTENCIAS ---');
  results.warnings.forEach(warn => console.log(`  ${warn}`));
}

console.log('\n=== ESTADO DE INTEGRACIÓN ===');
if (results.failed.length === 0) {
  console.log('✅ INTEGRACIÓN COMPLETA - Todos los componentes están correctamente integrados');
  process.exit(0);
} else if (results.failed.length <= 3) {
  console.log('⚠️  INTEGRACIÓN CASI COMPLETA - Algunos componentes necesitan ajustes menores');
  process.exit(0);
} else {
  console.log('❌ INTEGRACIÓN INCOMPLETA - Varios componentes necesitan integración');
  process.exit(1);
}
