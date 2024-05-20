import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './components/Landing';
import ProductDetails from './components/ProductDetails';
import SuccessPage from './components/SuccessPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>PenguinCo</h1>
        </header>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/purchase" element={<ProductDetails />} />
          <Route path="/success" element={<SuccessPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;