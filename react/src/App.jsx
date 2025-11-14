import { Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Home from './pages/Home'; 
import Products from './pages/Products';
import Cart from './pages/Cart';
import Profile from './pages/Profile';
import SellerDashboard from './pages/SellerDashboard';
import AdminDashboard from './pages/AdminDashboard'

function App() {
  const handleLoginSuccess = (userData) => {
    console.log("Usuario logueado:", userData);
  };

  return (
    <Routes>
      <Route path="/login" element={<Login onLoginSuccess={handleLoginSuccess} />} />
      <Route path="/" element={<Home />} />
      <Route path="/products" element={<Products />} />
      <Route path="/cart" element={<Cart />} />
      <Route path="/profile" element={<Profile />} />
      <Route path="/sellerdash" element={<SellerDashboard />} />
      <Route path='/admindash' element={<AdminDashboard/>} />
    </Routes>
  );
}

export default App;