import { useState } from 'react'
import Dog from './Dog.jsx'

function periodLabel(interval) {
  return interval === 'day' ? 'today' : `this ${interval}`
}

function TaskCard({ title, interval, startingStreak, startingCount }) {
  const [streak, setStreak] = useState(startingStreak)
  const [count, setCount] = useState(startingCount)

  function checkOff() {
    if (count === 0) {
      setStreak(streak + 1)
    }
    setCount(count + 1)
  }

  function undo() {
    if (count === 0) {
      return
    }
    if (count === 1) {
      setStreak(streak - 1)
    }
    setCount(count - 1)
  }

  return (
    <div className="task-card">
      <div className="task-header">
        <h2>{title}</h2>
        <span className="interval">Every {interval}</span>
      </div>

      <div className="dog-row">
        <Dog streak={streak} count={count} />
      </div>

      <p className="task-stats">
        {streak} {interval} streak · {count} {periodLabel(interval)}
      </p>

      <div className="task-actions">
        <button onClick={checkOff}>Check off</button>
        <button onClick={undo} disabled={count === 0}>
          Undo
        </button>
      </div>
    </div>
  )
}

export default TaskCard