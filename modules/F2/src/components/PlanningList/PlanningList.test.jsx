import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PlanningList from './PlanningList';
import { deferred } from '../../test-utils/deferred';
import { sessions } from '../../data/sessions';

const groupA = () =>
  sessions.filter((s) => s.group === 'A' || s.group === 'Promotion');

describe('PlanningList', () => {
  it('Loading: while the promise is pending, a loading state is perceptible', () => {
    const { promise } = deferred();
    const loadSessions = vi.fn(() => promise);
    render(<PlanningList loadSessions={loadSessions} />);
    expect(screen.getByRole('status')).toHaveTextContent(/loading/i);
  });

  it('Success: after resolution, titles are displayed and loading disappears', async () => {
    const { promise, resolve } = deferred();
    const loadSessions = vi.fn(() => promise);
    render(<PlanningList loadSessions={loadSessions} />);
    resolve(sessions);
    await waitFor(() =>
      expect(screen.queryByRole('status')).not.toBeInTheDocument(),
    );
    const list = await screen.findByRole('list');
    expect(within(list).getByText('React composants')).toBeInTheDocument();
  });

  it('Filter A + accessibility: requests group A, shows A and Promotion without B; accessible name "Group" and keyboard filter', async () => {
    const { promise: p1, resolve: r1 } = deferred();
    const loadSessions = vi.fn(() => p1);
    const user = userEvent.setup();
    render(<PlanningList loadSessions={loadSessions} />);
    r1(sessions);
    await waitFor(() =>
      expect(screen.queryByRole('status')).not.toBeInTheDocument(),
    );

    const { promise: p2, resolve: r2 } = deferred();
    loadSessions.mockReturnValueOnce(p2);

    const select = screen.getByRole('combobox', { name: 'Group' });
    await user.tab();
    expect(select).toHaveFocus();
    await userEvent.selectOptions(select, 'A');
    expect(loadSessions).toHaveBeenLastCalledWith({ group: 'A' });

    r2(groupA());
    await waitFor(() => expect(screen.getByRole('list')).toBeInTheDocument());
    const list = screen.getByRole('list');
    expect(within(list).getByText('React composants')).toBeInTheDocument();
    expect(within(list).getByText('Authentification')).toBeInTheDocument();
    expect(within(list).getByText('Données et SQL')).toBeInTheDocument();
    expect(within(list).getByText('Travail autonome')).toBeInTheDocument();
    expect(screen.queryByText('React événements')).not.toBeInTheDocument();
    expect(screen.queryByText('Revue de projet')).not.toBeInTheDocument();
  });

  it('Empty result: a [] response produces an explicit message, without old result', async () => {
    const { promise: p1, resolve: r1 } = deferred();
    const loadSessions = vi.fn(() => p1);
    const user = userEvent.setup();
    render(<PlanningList loadSessions={loadSessions} />);
    r1(sessions);
    await waitFor(() =>
      expect(screen.getByText('React composants')).toBeInTheDocument(),
    );

    const { promise: p2, resolve: r2 } = deferred();
    loadSessions.mockReturnValueOnce(p2);
    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: 'Group' }),
      'Promotion',
    );
    r2([]);
    await waitFor(() =>
      expect(screen.queryByText('React composants')).not.toBeInTheDocument(),
    );
    expect(screen.getByText(/no sessions/i)).toBeInTheDocument();
  });

  it('Error then retry: a rejection produces a visible error, "Retry" re-triggers the same request and recovers results', async () => {
    const { promise: p1, reject: rej1 } = deferred();
    const loadSessions = vi.fn(() => p1);
    const user = userEvent.setup();
    render(<PlanningList loadSessions={loadSessions} />);
    rej1(new Error('boom'));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toBeInTheDocument(),
    );
    expect(loadSessions).toHaveBeenCalledWith({ group: 'all' });

    const { promise: p2, resolve: r2 } = deferred();
    loadSessions.mockReturnValueOnce(p2);
    await userEvent.click(
      screen.getByRole('button', { name: /retry/i }),
    );
    expect(loadSessions).toHaveBeenLastCalledWith({ group: 'all' });
    r2(sessions);
    await waitFor(() =>
      expect(screen.getByText('React composants')).toBeInTheDocument(),
    );
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('Out-of-order responses: the late response of the first request does not replace the most recent', async () => {
    const d1 = deferred();
    const d2 = deferred();
    const loadSessions = vi.fn();
    loadSessions.mockReturnValueOnce(d1.promise);
    const user = userEvent.setup();
    render(<PlanningList loadSessions={loadSessions} />);
    loadSessions.mockReturnValueOnce(d2.promise);
    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: 'Group' }),
      'A',
    );
    d2.resolve(groupA());
    await waitFor(() =>
      expect(screen.getByText('React composants')).toBeInTheDocument(),
    );
    d1.resolve(sessions);
    await waitFor(() =>
      expect(screen.getByText('React composants')).toBeInTheDocument(),
    );
    expect(screen.queryByText('React événements')).not.toBeInTheDocument();
  });
});
