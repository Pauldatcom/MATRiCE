import { useEffect, useState } from 'react';

// F2 starting point — intentionally imperfect.
export default function PlanningList({ loadSessions }) {
  const [group, setGroup] = useState('all');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    loadSessions({ group }).then((result) => {
      setItems(result);
      setLoading(false);
    });
  }, [group, loadSessions]);

  return (
    <section>
      <h1>Planning</h1>
      <select
        aria-label="Group"
        value={group}
        onChange={(e) => setGroup(e.target.value)}
      >
        <option value="all">All</option>
        <option value="A">Group A</option>
        <option value="B">Group B</option>
        <option value="Promotion">Promotion</option>
      </select>
      {loading ? (
        <p role="status">Loading...</p>
      ) : (
        <ul>{items.map((s) => <li key={s.id}>{s.title}</li>)}</ul>
      )}
    </section>
  );
}
