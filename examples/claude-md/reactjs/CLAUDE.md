# CLAUDE.md - React.js project

This file provides guidance to Claude Code (claude.ai/code) when working with this React.js project.

## Project architecture

This is a **React.js application** built with TypeScript, using modern React patterns and a component-based architecture.

### Project structure
```
project/
├── public/                # Static assets
│   ├── index.html        # Main HTML template
│   └── favicon.ico       # Favicon
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── ui/          # Base UI components (Button, Input, etc.)
│   │   ├── layout/      # Layout components (Header, Footer, Sidebar)
│   │   └── features/    # Feature-specific components
│   ├── pages/           # Page components (route components)
│   ├── hooks/           # Custom React hooks
│   ├── store/           # State management (Zustand/Redux)
│   ├── services/        # API calls and external services
│   ├── utils/           # Utility functions
│   ├── types/           # TypeScript type definitions
│   ├── styles/          # Global styles and theme
│   ├── assets/          # Images, icons, fonts
│   ├── App.tsx          # Main application component
│   └── main.tsx         # Application entry point
├── tests/               # Test files
└── docs/               # Documentation
```

## Development commands

### Package management
```bash
# Install dependencies
npm install
# or
yarn install
# or
pnpm install

# Install specific package
npm install package-name
yarn add package-name
pnpm add package-name

# Install dev dependency
npm install -D package-name
yarn add -D package-name
pnpm add -D package-name
```

### Development server
```bash
# Start development server
npm run dev
# or
yarn dev
# or
pnpm dev

# Start with specific port
npm run dev -- --port 3001
```

### Building and production
```bash
# Build for production
npm run build
# or
yarn build
# or
pnpm build

# Preview production build
npm run preview
# or
yarn preview
# or
pnpm preview
```

### Testing
```bash
# Run tests
npm test
# or
npm run test
# or
yarn test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run end-to-end tests (if using Playwright/Cypress)
npm run test:e2e
```

### Code quality
```bash
# Lint code
npm run lint
# or
yarn lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Type checking
npm run type-check
```

## Technology stack

### Core framework
- **React 18+**: Modern React with concurrent features
- **TypeScript**: Static type checking
- **Vite**: Fast build tool and dev server

### State management
- **Zustand**: Lightweight state management
- **TanStack Query**: Server state management
- **React Context**: For global app state (theme, auth)

### Styling
- **Tailwind CSS**: Utility-first CSS framework
- **CSS Modules**: Component-scoped CSS (alternative)
- **styled-components**: CSS-in-JS (alternative)

### UI components
- **Radix UI**: Unstyled, accessible components
- **shadcn/ui**: Pre-built components with Tailwind
- **Heroicons**: Beautiful hand-crafted SVG icons

### Development tools
- **Vitest**: Unit testing framework
- **Testing Library**: React component testing utilities
- **Playwright**: End-to-end testing
- **ESLint**: JavaScript/TypeScript linter
- **Prettier**: Code formatter
- **Storybook**: Component development environment

## Component patterns

### Functional components with hooks
```tsx
// src/components/UserProfile.tsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { userService } from '../services/userService';

interface UserProfileProps {
  userId: string;
  onEdit?: () => void;
}

export const UserProfile: React.FC<UserProfileProps> = ({ userId, onEdit }) => {
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => userService.getById(userId),
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading user</div>;
  if (!user) return <div>User not found</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">{user.name}</h2>
        {onEdit && (
          <button
            onClick={onEdit}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Edit
          </button>
        )}
      </div>
      <p className="text-gray-600">{user.email}</p>
    </div>
  );
};
```

### Custom hooks
```tsx
// src/hooks/useLocalStorage.ts
import { useState, useEffect } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue] as const;
}
```

### State management with Zustand
```tsx
// src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({
        user,
        token,
        isAuthenticated: true,
      }),
      logout: () => set({
        user: null,
        token: null,
        isAuthenticated: false,
      }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

## Routing (React router)

```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { HomePage } from './pages/HomePage';
import { UserPage } from './pages/UserPage';
import { LoginPage } from './pages/LoginPage';
import { ProtectedRoute } from './components/ProtectedRoute';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route
              path="/users/:id"
              element={
                <ProtectedRoute>
                  <UserPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

## API integration

### Service layer
```tsx
// src/services/apiClient.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('auth-token');

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  post<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
```

### Data fetching with TanStack query
```tsx
// src/services/userService.ts
import { apiClient } from './apiClient';

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export const userService = {
  getById: (id: string): Promise<User> =>
    apiClient.get(`/users/${id}`),

  getAll: (): Promise<User[]> =>
    apiClient.get('/users'),

  create: (userData: Omit<User, 'id'>): Promise<User> =>
    apiClient.post('/users', userData),

  update: (id: string, userData: Partial<User>): Promise<User> =>
    apiClient.put(`/users/${id}`, userData),

  delete: (id: string): Promise<void> =>
    apiClient.delete(`/users/${id}`),
};

// Usage in component
export const useUsers = () => {
  return useQuery({
    queryKey: ['users'],
    queryFn: userService.getAll,
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: userService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};
```

## Environment configuration

### Environment variables
```bash
# .env.local
VITE_API_URL=http://localhost:3000/api
VITE_APP_NAME=My React App
VITE_ENABLE_ANALYTICS=false
```

### Configuration management
```tsx
// src/config/env.ts
interface Config {
  apiUrl: string;
  appName: string;
  enableAnalytics: boolean;
}

export const config: Config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:3000/api',
  appName: import.meta.env.VITE_APP_NAME || 'React App',
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
};
```

## Vite configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/utils': path.resolve(__dirname, './src/utils'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

## Package.json scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write .",
    "type-check": "tsc --noEmit",
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build"
  }
}
```
