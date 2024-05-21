import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ErrorPage from './components/ErrorPage';
import Header from './components/Header';
import Landing from './components/Landing';
import PaymentForm from './components/PaymentForm';
import ProductDetails from './components/ProductDetails';
import SuccessPage from './components/SuccessPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/error" element={<ErrorPage />} />
          <Route path="/payment" element={<PaymentForm />} />
          <Route path="/purchase" element={<ProductDetails />} />
          <Route path="/success" element={<SuccessPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;