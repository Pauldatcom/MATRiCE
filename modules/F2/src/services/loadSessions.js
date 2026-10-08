import { sessions } from '../data/sessions';

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export async function loadSessions({ group }) {
  await delay(300);
  return sessions.filter(
    (s) =>
      group === 'all' ||
      s.group === group ||
      (['A', 'B'].includes(group) && s.group === 'Promotion'),
  );
}