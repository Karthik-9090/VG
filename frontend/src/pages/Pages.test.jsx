import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';
import '@testing-library/jest-dom';

// Mock the API calls
jest.mock('../api/client');

describe('Auth Pages', () => {
  test('Login page renders with email and password fields', () => {
    const Login = require('../pages/Login').default;
    render(
      <BrowserRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
  });

  test('Register page renders with name, email, and password fields', () => {
    const Register = require('../pages/Register').default;
    render(
      <BrowserRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
  });
});

describe('Dashboard Page', () => {
  test('Dashboard renders with heading', () => {
    const Dashboard = require('../pages/Dashboard').default;
    render(
      <BrowserRouter>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </BrowserRouter>
    );

    // Dashboard might be loading initially, so check for either loading or heading
    const dashboardHeading = screen.queryByText(/dashboard/i);
    const loadingText = screen.queryByText(/loading/i);
    expect(dashboardHeading || loadingText).toBeTruthy();
  });
});

describe('Layout Component', () => {
  test('Layout renders navigation menu', () => {
    const Layout = require('../pages/Layout').default;
    render(
      <BrowserRouter>
        <AuthProvider>
          <Layout />
        </AuthProvider>
      </BrowserRouter>
    );

    const vayuGuardElements = screen.getAllByText(/VayuGuard/i);
    expect(vayuGuardElements.length).toBeGreaterThan(0);
  });
});

describe('Forecast Page', () => {
  test('Forecast page renders city and horizon selectors', () => {
    const Forecast = require('../pages/Forecast').default;
    render(
      <BrowserRouter>
        <AuthProvider>
          <Forecast />
        </AuthProvider>
      </BrowserRouter>
    );

    expect(screen.getByLabelText(/^city$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/horizon/i)).toBeInTheDocument();
  });
});

describe('Profile Page', () => {
  test('Profile page renders', () => {
    const Profile = require('../pages/Profile').default;
    render(
      <BrowserRouter>
        <AuthProvider>
          <Profile />
        </AuthProvider>
      </BrowserRouter>
    );

    // Just verify the component renders without crashing
    expect(screen.queryByText(/loading/i)).toBeInTheDocument();
  });
});

describe('NotFound Page', () => {
  test('NotFound page renders 404 message', () => {
    const NotFound = require('../pages/NotFound').default;
    render(
      <BrowserRouter>
        <NotFound />
      </BrowserRouter>
    );

    expect(screen.getByText(/404/i)).toBeInTheDocument();
  });
});
