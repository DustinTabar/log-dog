import { useState } from 'react'
import { Link } from 'react-router'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    setMessage(`Would log in as ${email}`)
  }

  return (
    <>
      <h1>Log in</h1>
      <form className="auth-form" onSubmit={handleSubmit}>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        <button type="submit">Log in</button>
      </form>

      {message && <p>{message}</p>}

      <p>
        No account yet? <Link to="/register">Sign up</Link>
      </p>
    </>
  )
}

export default LoginPage