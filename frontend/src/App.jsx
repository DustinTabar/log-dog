import { Link, Navigate, Route, Routes } from 'react-router'
import DashboardPage from './pages/DashboardPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import './App.css'

function App() {
  return (
    <main>
      <nav>
        <Link to="/dashboard">Dashboard</Link> | <Link to="/login">Log in</Link> |{' '}
        <Link to="/register">Sign up</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="*" element={<h1>Page not found</h1>} />
      </Routes>
    </main>
  )
}

export default App