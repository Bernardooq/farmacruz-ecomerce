import { Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import Home from './pages/Home';

function App() {
  const handleLoginSuccess = (userData) => {
    console.log("Usuario logueado:", userData);
  };

  return (
    <Routes>
      <Route path="/" element={<Login onLoginSuccess={handleLoginSuccess} />} />
      <Route path="/home" element={<Home />} />
    </Routes>
  );
}

export default App;
