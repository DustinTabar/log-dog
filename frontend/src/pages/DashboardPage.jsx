import TaskCard from '../components/TaskCard.jsx'

const fakeTasks = [
  { id: 1, title: 'Brush teeth', interval: 'day', streak: 12, periodCount: 2 },
  { id: 2, title: 'Walk the dog', interval: 'day', streak: 5, periodCount: 1 },
  { id: 3, title: 'Gym', interval: 'week', streak: 3, periodCount: 0 },
  { id: 4, title: 'Call mom', interval: 'month', streak: 0, periodCount: 0 },
]

function DashboardPage() {
  return (
    <>
      <h1>Your tasks</h1>
      {fakeTasks.map((task) => (
        <TaskCard
          key={task.id}
          title={task.title}
          interval={task.interval}
          startingStreak={task.streak}
          startingCount={task.periodCount}
        />
      ))}
    </>
  )
}

export default DashboardPage