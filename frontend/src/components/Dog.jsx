const SEGMENT_WIDTH = 10
const MAX_SEGMENTS = 25
const BASE_BODY_WIDTH = 60

function Dog({ streak, count }) {
  const segments = Math.min(streak, MAX_SEGMENTS)
  const bodyWidth = BASE_BODY_WIDTH + segments * SEGMENT_WIDTH

  const bodyX = 20
  const headX = bodyX + bodyWidth + 6
  const width = headX + 42

  return (
    <svg
      width={width}
      height={72}
      viewBox={`0 0 ${width} 72`}
      role="img"
      aria-label={`Dog with a streak of ${streak}`}
    >
      {/* tail */}
      <path d={`M ${bodyX + 4} 32 Q 6 26 4 12`} stroke="#8b4a1c" strokeWidth="5" fill="none" strokeLinecap="round" />

      {/* legs */}
      <rect x={bodyX + 8} y={44} width={7} height={18} rx={3} fill="#8b4a1c" />
      <rect x={bodyX + 20} y={44} width={7} height={18} rx={3} fill="#8b4a1c" />
      <rect x={bodyX + bodyWidth - 27} y={44} width={7} height={18} rx={3} fill="#8b4a1c" />
      <rect x={bodyX + bodyWidth - 15} y={44} width={7} height={18} rx={3} fill="#8b4a1c" />

      {/* body */}
      <rect x={bodyX} y={24} width={bodyWidth} height={28} rx={14} fill="#b5651d" />

      {/* head */}
      <circle cx={headX} cy={26} r={16} fill="#b5651d" />
      <ellipse cx={headX + 16} cy={32} rx={11} ry={7} fill="#b5651d" />
      <ellipse cx={headX - 5} cy={30} rx={6} ry={12} fill="#8b4a1c" />
      <circle cx={headX + 5} cy={21} r={2.5} fill="#222" />
      <circle cx={headX + 26} cy={30} r={3.5} fill="#222" />

      {/* count inside the body */}
      <text
        x={bodyX + bodyWidth / 2}
        y={43}
        textAnchor="middle"
        fontSize="16"
        fontWeight="bold"
        fill="#fff"
      >
        {count}
      </text>
    </svg>
  )
}

export default Dog