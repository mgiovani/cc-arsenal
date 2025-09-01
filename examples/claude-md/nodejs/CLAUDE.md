# CLAUDE.md - Node.js Project

This file provides guidance to Claude Code (claude.ai/code) when working with this Node.js project.

## Project Architecture

This is a **Node.js application** built with TypeScript, following clean architecture principles and modern development practices.

### Project Structure
```
project/
├── src/
│   ├── controllers/        # HTTP request handlers
│   ├── services/          # Business logic layer
│   ├── models/            # Data models and database schemas
│   ├── middleware/        # Express middleware functions
│   ├── routes/            # API route definitions
│   ├── utils/             # Utility functions and helpers
│   ├── types/             # TypeScript type definitions
│   ├── config/            # Configuration files
│   └── app.ts            # Express application setup
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test data
├── dist/                 # Compiled JavaScript (build output)
├── docs/                 # API documentation
└── scripts/              # Build and deployment scripts
```

## Development Commands

### Package Management
```bash
# Install dependencies
npm install
# or
yarn install

# Install development dependencies
npm install --save-dev
# or
yarn add --dev

# Update dependencies
npm update
# or
yarn upgrade
```

### Development Server
```bash
# Run development server with hot reload
npm run dev
# or
yarn dev

# Run with debugging
npm run dev:debug
# or
yarn dev:debug
```

### Building and Production
```bash
# Build TypeScript to JavaScript
npm run build
# or
yarn build

# Start production server
npm start
# or
yarn start

# Build and start
npm run build && npm start
```

### Testing
```bash
# Run all tests
npm test
# or
yarn test

# Run tests in watch mode
npm run test:watch
# or
yarn test:watch

# Run tests with coverage
npm run test:coverage
# or
yarn test:coverage

# Run integration tests
npm run test:integration
# or
yarn test:integration
```

### Code Quality
```bash
# Lint code
npm run lint
# or
yarn lint

# Fix linting issues
npm run lint:fix
# or
yarn lint:fix

# Format code
npm run format
# or
yarn format

# Type checking
npm run type-check
# or
yarn type-check
```

### Database Operations (if using Prisma)
```bash
# Generate Prisma client
npx prisma generate

# Run database migrations
npx prisma migrate dev

# Reset database
npx prisma migrate reset

# Open Prisma Studio
npx prisma studio

# Push schema changes (development)
npx prisma db push
```

## Technology Stack

### Core Framework
- **Express.js**: Fast, unopinionated web framework
- **TypeScript**: Typed superset of JavaScript
- **Node.js**: JavaScript runtime

### Database & ORM
- **Prisma**: Next-generation ORM for Node.js
- **PostgreSQL**: Primary database
- **Redis**: Caching and session storage

### Authentication & Security
- **jsonwebtoken**: JWT implementation
- **bcrypt**: Password hashing
- **helmet**: Security middleware
- **cors**: Cross-origin resource sharing

### Development Tools
- **Jest**: Testing framework
- **Supertest**: HTTP assertion library
- **ESLint**: JavaScript linter
- **Prettier**: Code formatter
- **ts-node**: TypeScript execution
- **nodemon**: Development server with hot reload

## API Conventions

### Response Format
```typescript
// Success response
interface SuccessResponse<T> {
  success: true;
  data: T;
  message?: string;
}

// Error response
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
}
```

### Route Structure
```typescript
// src/routes/users.ts
import express from 'express';
import { UserController } from '../controllers/UserController';
import { authMiddleware } from '../middleware/auth';
import { validateRequest } from '../middleware/validation';
import { createUserSchema } from '../schemas/user';

const router = express.Router();
const userController = new UserController();

router.post(
  '/',
  validateRequest(createUserSchema),
  userController.create
);

router.get(
  '/:id',
  authMiddleware,
  userController.getById
);

export default router;
```

### Controller Pattern
```typescript
// src/controllers/UserController.ts
import { Request, Response, NextFunction } from 'express';
import { UserService } from '../services/UserService';

export class UserController {
  private userService = new UserService();

  create = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const user = await this.userService.createUser(req.body);
      res.status(201).json({
        success: true,
        data: user,
        message: 'User created successfully'
      });
    } catch (error) {
      next(error);
    }
  };

  getById = async (req: Request, res: Response, next: NextFunction) => {
    try {
      const user = await this.userService.getUserById(req.params.id);
      res.json({
        success: true,
        data: user
      });
    } catch (error) {
      next(error);
    }
  };
}
```

## Common Patterns

### Error Handling Middleware
```typescript
// src/middleware/errorHandler.ts
import { Request, Response, NextFunction } from 'express';

export class AppError extends Error {
  statusCode: number;
  isOperational: boolean;

  constructor(message: string, statusCode: number) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = true;

    Error.captureStackTrace(this, this.constructor);
  }
}

export const errorHandler = (
  error: Error,
  req: Request,
  res: Response,
  next: NextFunction
) => {
  if (error instanceof AppError) {
    return res.status(error.statusCode).json({
      success: false,
      error: {
        code: error.constructor.name,
        message: error.message
      }
    });
  }

  // Handle unexpected errors
  console.error('Unexpected error:', error);
  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_SERVER_ERROR',
      message: 'Something went wrong'
    }
  });
};
```

### Request Validation
```typescript
// src/middleware/validation.ts
import { Request, Response, NextFunction } from 'express';
import { z } from 'zod';

export const validateRequest = (schema: z.ZodSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      schema.parse(req.body);
      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid request data',
            details: error.errors
          }
        });
      }
      next(error);
    }
  };
};
```

### Service Layer
```typescript
// src/services/UserService.ts
import { PrismaClient } from '@prisma/client';
import { AppError } from '../middleware/errorHandler';

export class UserService {
  private prisma = new PrismaClient();

  async createUser(userData: CreateUserData): Promise<User> {
    const existingUser = await this.prisma.user.findUnique({
      where: { email: userData.email }
    });

    if (existingUser) {
      throw new AppError('User already exists', 409);
    }

    return await this.prisma.user.create({
      data: userData
    });
  }

  async getUserById(id: string): Promise<User | null> {
    const user = await this.prisma.user.findUnique({
      where: { id }
    });

    if (!user) {
      throw new AppError('User not found', 404);
    }

    return user;
  }
}
```

## Environment Configuration

### Required Environment Variables
```bash
# Server
PORT=3000
NODE_ENV=development

# Database
DATABASE_URL="postgresql://username:password@localhost:5432/mydb"
REDIS_URL="redis://localhost:6379"

# Authentication
JWT_SECRET=your-jwt-secret-key
JWT_EXPIRES_IN=7d

# External APIs
API_KEY=your-api-key
```

### Configuration Management
```typescript
// src/config/index.ts
import { z } from 'zod';

const configSchema = z.object({
  port: z.number().default(3000),
  nodeEnv: z.enum(['development', 'production', 'test']).default('development'),
  databaseUrl: z.string(),
  redisUrl: z.string(),
  jwtSecret: z.string(),
  jwtExpiresIn: z.string().default('7d'),
});

type Config = z.infer<typeof configSchema>;

export const config: Config = configSchema.parse({
  port: Number(process.env.PORT),
  nodeEnv: process.env.NODE_ENV,
  databaseUrl: process.env.DATABASE_URL,
  redisUrl: process.env.REDIS_URL,
  jwtSecret: process.env.JWT_SECRET,
  jwtExpiresIn: process.env.JWT_EXPIRES_IN,
});
```

## Package.json Scripts

```json
{
  "scripts": {
    "dev": "nodemon src/app.ts",
    "dev:debug": "nodemon --inspect src/app.ts",
    "build": "tsc",
    "start": "node dist/app.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:integration": "jest --testPathPattern=tests/integration",
    "lint": "eslint src/ --ext .ts",
    "lint:fix": "eslint src/ --ext .ts --fix",
    "format": "prettier --write src/",
    "type-check": "tsc --noEmit"
  }
}
```

## Docker Configuration

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY dist/ ./dist/

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

CMD ["node", "dist/app.js"]
```
