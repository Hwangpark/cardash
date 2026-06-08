import { useNavigate } from 'react-router-dom'

export default function Navbar() {
  const navigate = useNavigate()
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <button className="navbar-logo" onClick={() => navigate('/')}>
          <span className="logo-icon">🚗</span>
          <span className="logo-text">CarDash</span>
        </button>
        <span className="navbar-sub">국내 중고차 통합 분석</span>
      </div>
    </nav>
  )
}
