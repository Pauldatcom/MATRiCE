import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PlanningList from './PlanningList';
import { deferred } from '../../test-utils/deferred';
import { sessions } from '../../data/sessions';

const groupA = () =>
  sessions.filter((s) => s.group === 'A' || s.group === 'Promotion');

describe('PlanningList', () => {
  it('Chargement: tant que la promesse est en attente, un état de chargement est perceptible', () => {
    const { promise } = deferred();
    const loadSessions = vi.fn(() => promise);
    render(<PlanningList loadSessions={loadSessions} />);
    expect(screen.getByRole('status')).toHaveTextContent(/chargement/i);
  });

  it('Succès: après résolution, les titres sont affichés et le chargement disparaît', async () => {
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

  it('Filtre A + accessibilité: demande le groupe A, affiche A et Promotion sans B ; nom accessible « Groupe » et filtre au clavier', async () => {
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

    const select = screen.getByRole('combobox', { name: 'Groupe' });
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

  it('Résultat vide: une réponse [] produit un message explicite, sans ancien résultat', async () => {
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
      screen.getByRole('combobox', { name: 'Groupe' }),
      'Promotion',
    );
    r2([]);
    await waitFor(() =>
      expect(screen.queryByText('React composants')).not.toBeInTheDocument(),
    );
    expect(screen.getByText(/aucune séance/i)).toBeInTheDocument();
  });

  it('Erreur puis nouvelle tentative: un rejet produit une erreur visible, « Réessayer » relance la même demande et retrouve les résultats', async () => {
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
      screen.getByRole('button', { name: /réessayer/i }),
    );
    expect(loadSessions).toHaveBeenLastCalledWith({ group: 'all' });
    r2(sessions);
    await waitFor(() =>
      expect(screen.getByText('React composants')).toBeInTheDocument(),
    );
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('Réponses désordonnées: la réponse tardive de la première demande ne remplace pas la plus récente', async () => {
    const d1 = deferred();
    const d2 = deferred();
    const loadSessions = vi.fn();
    loadSessions.mockReturnValueOnce(d1.promise);
    const user = userEvent.setup();
    render(<PlanningList loadSessions={loadSessions} />);
    loadSessions.mockReturnValueOnce(d2.promise);
    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: 'Groupe' }),
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