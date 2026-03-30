/**
 * Comprehensive unit tests for server.js
 * Tests Express app configuration, middleware setup, routing, and startup sequence
 */

// Mock all external dependencies before requiring server.js
jest.mock('dotenv', () => ({
  config: jest.fn()
}));

jest.mock('express', () => {
  const mockExpress = jest.fn(() => ({
    use: jest.fn(),
    listen: jest.fn((port, host, callback) => {
      callback();
      return { close: jest.fn() };
    })
  }));
  mockExpress.json = jest.fn(() => 'express.json middleware');
  return mockExpress;
});

jest.mock('cookie-parser', () => jest.fn(() => 'cookie-parser middleware'));
jest.mock('helmet', () => jest.fn(() => 'helmet middleware'));
jest.mock('cors', () => jest.fn(() => 'cors middleware'));

jest.mock('../config/database', () => ({
  initDatabase: jest.fn()
}));

jest.mock('../config/redis', () => ({
  initRedis: jest.fn()
}));

jest.mock('../middleware/secrets', () => ({
  loadConfig: jest.fn()
}));

jest.mock('../routes/users', () => 'users router');
jest.mock('../routes/files', () => 'files router');
jest.mock('../routes/health', () => 'health router');

describe('server.js', () => {
  let express;
  let helmet;
  let cors;
  let cookieParser;
  let initDatabase;
  let initRedis;
  let loadConfig;
  let mockApp;
  let consoleLogSpy;
  let consoleErrorSpy;
  let processExitSpy;

  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    jest.resetModules();

    // Get mock references
    express = require('express');
    helmet = require('helmet');
    cors = require('cors');
    cookieParser = require('cookie-parser');
    initDatabase = require('../config/database').initDatabase;
    initRedis = require('../config/redis').initRedis;
    loadConfig = require('../middleware/secrets').loadConfig;

    // Create mock app instance
    mockApp = {
      use: jest.fn(),
      listen: jest.fn((port, host, callback) => {
        if (callback) callback();
        return { close: jest.fn() };
      })
    };
    express.mockReturnValue(mockApp);

    // Setup console spies
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    processExitSpy = jest.spyOn(process, 'exit').mockImplementation();

    // Setup default successful async mocks
    loadConfig.mockResolvedValue();
    initDatabase.mockResolvedValue();
    initRedis.mockResolvedValue();
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
    processExitSpy.mockRestore();
  });

  describe('Module initialization', () => {
    test('should load dotenv configuration on module load', () => {
      const dotenv = require('dotenv');
      require('../server');
      expect(dotenv.config).toHaveBeenCalledTimes(1);
    });

    test('should import all required dependencies', () => {
      require('../server');
      expect(express).toHaveBeenCalled();
      expect(helmet).toHaveBeenCalled();
      expect(cookieParser).toHaveBeenCalled();
    });
  });

  describe('Express app configuration', () => {
    test('should create Express application instance', () => {
      require('../server');
      expect(express).toHaveBeenCalledTimes(1);
    });

    test('should configure helmet middleware first', () => {
      require('../server');
      expect(helmet).toHaveBeenCalled();
      expect(mockApp.use).toHaveBeenCalledWith('helmet middleware');
    });

    test('should configure CORS with credentials and ALLOWED_ORIGIN from env', () => {
      process.env.ALLOWED_ORIGIN = 'https://example.com';
      require('../server');
      expect(cors).toHaveBeenCalledWith({
        origin: 'https://example.com',
        credentials: true
      });
      expect(mockApp.use).toHaveBeenCalledWith('cors middleware');
      delete process.env.ALLOWED_ORIGIN;
    });

    test('should configure CORS with undefined origin when ALLOWED_ORIGIN not set', () => {
      delete process.env.ALLOWED_ORIGIN;
      require('../server');
      expect(cors).toHaveBeenCalledWith({
        origin: undefined,
        credentials: true
      });
    });

    test('should configure express.json with 1mb limit', () => {
      require('../server');
      expect(express.json).toHaveBeenCalledWith({ limit: '1mb' });
      expect(mockApp.use).toHaveBeenCalledWith('express.json middleware');
    });

    test('should configure cookie-parser middleware', () => {
      require('../server');
      expect(cookieParser).toHaveBeenCalled();
      expect(mockApp.use).toHaveBeenCalledWith('cookie-parser middleware');
    });

    test('should mount health router at /health', () => {
      require('../server');
      expect(mockApp.use).toHaveBeenCalledWith('/health', 'health router');
    });

    test('should mount users router at /api/users', () => {
      require('../server');
      expect(mockApp.use).toHaveBeenCalledWith('/api/users', 'users router');
    });

    test('should mount files router at /api/files', () => {
      require('../server');
      expect(mockApp.use).toHaveBeenCalledWith('/api/files', 'files router');
    });

    test('should configure middleware in correct order', () => {
      require('../server');
      const calls = mockApp.use.mock.calls;

      // Verify order: helmet, cors, json, cookieParser, then routes
      expect(calls[0][0]).toBe('helmet middleware');
      expect(calls[1][0]).toBe('cors middleware');
      expect(calls[2][0]).toBe('express.json middleware');
      expect(calls[3][0]).toBe('cookie-parser middleware');
      expect(calls[4]).toEqual(['/health', 'health router']);
      expect(calls[5]).toEqual(['/api/users', 'users router']);
      expect(calls[6]).toEqual(['/api/files', 'files router']);
    });
  });

  describe('start() function - successful startup', () => {
    test('should call loadConfig, initDatabase, initRedis in sequence', async () => {
      const callOrder = [];
      loadConfig.mockImplementation(() => {
        callOrder.push('loadConfig');
        return Promise.resolve();
      });
      initDatabase.mockImplementation(() => {
        callOrder.push('initDatabase');
        return Promise.resolve();
      });
      initRedis.mockImplementation(() => {
        callOrder.push('initRedis');
        return Promise.resolve();
      });

      require('../server');

      // Wait for start() to complete
      await new Promise(resolve => setTimeout(resolve, 100));

      expect(loadConfig).toHaveBeenCalledTimes(1);
      expect(initDatabase).toHaveBeenCalledTimes(1);
      expect(initRedis).toHaveBeenCalledTimes(1);
      expect(callOrder).toEqual(['loadConfig', 'initDatabase', 'initRedis']);
    });

    test('should start server on default port 8080 when PORT not set', async () => {
      delete process.env.PORT;
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockApp.listen).toHaveBeenCalledWith(
        8080,
        '0.0.0.0',
        expect.any(Function)
      );
    });

    test('should start server on custom PORT from environment', async () => {
      process.env.PORT = '3000';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockApp.listen).toHaveBeenCalledWith(
        '3000',
        '0.0.0.0',
        expect.any(Function)
      );
      delete process.env.PORT;
    });

    test('should bind server to 0.0.0.0 for EC2 deployment', async () => {
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockApp.listen).toHaveBeenCalledWith(
        expect.any(Number),
        '0.0.0.0',
        expect.any(Function)
      );
    });

    test('should log server startup message with port and environment', async () => {
      process.env.PORT = '9000';
      process.env.ENVIRONMENT = 'production';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        'Server listening on port 9000 (env=production)'
      );
      delete process.env.PORT;
      delete process.env.ENVIRONMENT;
    });

    test('should log environment as undefined when ENVIRONMENT not set', async () => {
      delete process.env.ENVIRONMENT;
      process.env.PORT = '8080';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        'Server listening on port 8080 (env=undefined)'
      );
    });
  });

  describe('start() function - error handling', () => {
    test('should exit with code 1 when loadConfig fails', async () => {
      const error = new Error('Failed to load configuration');
      loadConfig.mockRejectedValue(error);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleErrorSpy).toHaveBeenCalledWith('Fatal startup error:', error);
      expect(processExitSpy).toHaveBeenCalledWith(1);
      expect(mockApp.listen).not.toHaveBeenCalled();
    });

    test('should exit with code 1 when initDatabase fails', async () => {
      const error = new Error('Database connection failed');
      initDatabase.mockRejectedValue(error);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleErrorSpy).toHaveBeenCalledWith('Fatal startup error:', error);
      expect(processExitSpy).toHaveBeenCalledWith(1);
      expect(mockApp.listen).not.toHaveBeenCalled();
    });

    test('should exit with code 1 when initRedis fails', async () => {
      const error = new Error('Redis connection failed');
      initRedis.mockRejectedValue(error);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleErrorSpy).toHaveBeenCalledWith('Fatal startup error:', error);
      expect(processExitSpy).toHaveBeenCalledWith(1);
      expect(mockApp.listen).not.toHaveBeenCalled();
    });

    test('should not call initDatabase if loadConfig fails', async () => {
      loadConfig.mockRejectedValue(new Error('Config load failed'));

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(loadConfig).toHaveBeenCalled();
      expect(initDatabase).not.toHaveBeenCalled();
      expect(initRedis).not.toHaveBeenCalled();
    });

    test('should not call initRedis if initDatabase fails', async () => {
      initDatabase.mockRejectedValue(new Error('DB init failed'));

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(loadConfig).toHaveBeenCalled();
      expect(initDatabase).toHaveBeenCalled();
      expect(initRedis).not.toHaveBeenCalled();
    });
  });

  describe('Boundary value tests - PORT configuration', () => {
    test('should handle PORT as string "0" (minimum valid port)', async () => {
      process.env.PORT = '0';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockApp.listen).toHaveBeenCalledWith(
        '0',
        '0.0.0.0',
        expect.any(Function)
      );
      delete process.env.PORT;
    });

    test('should handle PORT as string "65535" (maximum valid port)', async () => {
      process.env.PORT = '65535';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockApp.listen).toHaveBeenCalledWith(
        '65535',
        '0.0.0.0',
        expect.any(Function)
      );
      delete process.env.PORT;
    });

    test('should handle PORT as empty string (use default)', async () => {
      process.env.PORT = '';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      // Empty string is falsy, should use default 8080
      expect(mockApp.listen).toHaveBeenCalledWith(
        8080,
        '0.0.0.0',
        expect.any(Function)
      );
      delete process.env.PORT;
    });

    test('should handle common port values (3000, 5000, 8000)', async () => {
      const ports = ['3000', '5000', '8000'];

      for (const port of ports) {
        jest.resetModules();
        jest.clearAllMocks();

        const express = require('express');
        const mockApp = {
          use: jest.fn(),
          listen: jest.fn((port, host, callback) => {
            if (callback) callback();
            return { close: jest.fn() };
          })
        };
        express.mockReturnValue(mockApp);

        process.env.PORT = port;
        require('../server');

        await new Promise(resolve => setTimeout(resolve, 50));

        expect(mockApp.listen).toHaveBeenCalledWith(
          port,
          '0.0.0.0',
          expect.any(Function)
        );
      }

      delete process.env.PORT;
    });
  });

  describe('Boundary value tests - ALLOWED_ORIGIN configuration', () => {
    test('should handle empty ALLOWED_ORIGIN', () => {
      process.env.ALLOWED_ORIGIN = '';
      require('../server');
      expect(cors).toHaveBeenCalledWith({
        origin: '',
        credentials: true
      });
      delete process.env.ALLOWED_ORIGIN;
    });

    test('should handle localhost ALLOWED_ORIGIN', () => {
      process.env.ALLOWED_ORIGIN = 'http://localhost:3000';
      require('../server');
      expect(cors).toHaveBeenCalledWith({
        origin: 'http://localhost:3000',
        credentials: true
      });
      delete process.env.ALLOWED_ORIGIN;
    });

    test('should handle wildcard ALLOWED_ORIGIN', () => {
      process.env.ALLOWED_ORIGIN = '*';
      require('../server');
      expect(cors).toHaveBeenCalledWith({
        origin: '*',
        credentials: true
      });
      delete process.env.ALLOWED_ORIGIN;
    });

    test('should handle HTTPS ALLOWED_ORIGIN with port', () => {
      process.env.ALLOWED_ORIGIN = 'https://example.com:8443';
      require('../server');
      expect(cors).toHaveBeenCalledWith({
        origin: 'https://example.com:8443',
        credentials: true
      });
      delete process.env.ALLOWED_ORIGIN;
    });

    test('should handle very long ALLOWED_ORIGIN URL', () => {
      const longOrigin = 'https://very-long-subdomain-name-for-testing-purposes.example-domain.com:9999';
      process.env.ALLOWED_ORIGIN = longOrigin;
      require('../server');
      expect(cors).toHaveBeenCalledWith({
        origin: longOrigin,
        credentials: true
      });
      delete process.env.ALLOWED_ORIGIN;
    });
  });

  describe('Boundary value tests - ENVIRONMENT configuration', () => {
    test('should handle undefined ENVIRONMENT', async () => {
      delete process.env.ENVIRONMENT;
      process.env.PORT = '8080';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        'Server listening on port 8080 (env=undefined)'
      );
    });

    test('should handle empty ENVIRONMENT', async () => {
      process.env.ENVIRONMENT = '';
      process.env.PORT = '8080';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        'Server listening on port 8080 (env=)'
      );
      delete process.env.ENVIRONMENT;
    });

    test('should handle standard ENVIRONMENT values', async () => {
      const environments = ['development', 'staging', 'production', 'test'];

      for (const env of environments) {
        jest.resetModules();
        jest.clearAllMocks();

        consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();

        const express = require('express');
        const mockApp = {
          use: jest.fn(),
          listen: jest.fn((port, host, callback) => {
            if (callback) callback();
            return { close: jest.fn() };
          })
        };
        express.mockReturnValue(mockApp);

        process.env.ENVIRONMENT = env;
        process.env.PORT = '8080';
        require('../server');

        await new Promise(resolve => setTimeout(resolve, 50));

        expect(consoleLogSpy).toHaveBeenCalledWith(
          `Server listening on port 8080 (env=${env})`
        );

        consoleLogSpy.mockRestore();
      }

      delete process.env.ENVIRONMENT;
      delete process.env.PORT;
    });
  });

  describe('Integration - complete startup flow', () => {
    test('should complete full startup sequence successfully', async () => {
      process.env.PORT = '8080';
      process.env.ENVIRONMENT = 'production';
      process.env.ALLOWED_ORIGIN = 'https://example.com';

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      // Verify all initialization steps
      expect(loadConfig).toHaveBeenCalledTimes(1);
      expect(initDatabase).toHaveBeenCalledTimes(1);
      expect(initRedis).toHaveBeenCalledTimes(1);

      // Verify server started
      expect(mockApp.listen).toHaveBeenCalledWith(
        '8080',
        '0.0.0.0',
        expect.any(Function)
      );

      // Verify log message
      expect(consoleLogSpy).toHaveBeenCalledWith(
        'Server listening on port 8080 (env=production)'
      );

      // Verify no errors
      expect(consoleErrorSpy).not.toHaveBeenCalled();
      expect(processExitSpy).not.toHaveBeenCalled();

      delete process.env.PORT;
      delete process.env.ENVIRONMENT;
      delete process.env.ALLOWED_ORIGIN;
    });
  });
});
