import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import Catalogue from '../src/Catalogue.jsx';

const tools = [
  { id: 1, name: 'Perceuse', category: 'Perçage', status: 'lent', description: 'Sans fil' },
  { id: 2, name: 'Taille-haie', category: 'Jardinage', status: 'available', description: '' },
  { id: 3, name: 'Ponceuse', category: 'Autre', status: 'unavailable', description: '' },
];

beforeEach(() => { vi.stubGlobal('fetch', vi.fn()); });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function respond(data, ok = true) { fetch.mockResolvedValue({ ok, json: async () => data, status: 500 }); }

describe('US-01 catalogue des outils', () => {
  it('affiche le nom, la catégorie et le statut en français de chaque outil', async () => {
    respond(tools);
    render(<Catalogue />);
    const item = await screen.findByRole('heading', { name: 'Perceuse' });
    const card = item.closest('li');
    expect(within(card).getByText('Perçage')).toBeInTheDocument();
    expect(within(card).getByText('Prêté')).toBeInTheDocument();
    expect(screen.getByText('Disponible')).toBeInTheDocument();
    expect(screen.getByText('Indisponible')).toBeInTheDocument();
  });
  it('place les outils disponibles avant les autres', async () => {
    respond(tools);
    render(<Catalogue />);
    await screen.findByRole('heading', { name: 'Taille-haie' });
    expect(screen.getAllByRole('listitem')[0]).toHaveTextContent('Taille-haie');
  });
  it('affiche le message demandé pour un catalogue vide', async () => {
    respond([]);
    render(<Catalogue />);
    expect(await screen.findByText('Aucun outil pour le moment')).toBeInTheDocument();
  });
  it('affiche une erreur si l’API échoue', async () => {
    respond(null, false);
    render(<Catalogue />);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Impossible de charger'));
  });
});
