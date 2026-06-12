import React from 'react';
import { MemoryRouter, Outlet, Route, Routes } from 'react-router-dom';
import { render } from '@testing-library/react';

const defaultOutletContext = {
    isMobile: false,
    language: 'en',
};

const OutletLayout = ({ context = defaultOutletContext }) => <Outlet context={context} />;

export const renderWithOutlet = (
    ui,
    {
        route = '/',
        path = '/',
        outletContext = defaultOutletContext,
    } = {},
) => render(
    <MemoryRouter initialEntries={[route]}>
        <Routes>
            <Route element={<OutletLayout context={outletContext} />}>
                <Route path={path} element={ui} />
            </Route>
        </Routes>
    </MemoryRouter>,
);
