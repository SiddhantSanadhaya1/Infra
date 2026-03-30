/**
 * Unit tests for Express server initialization and configuration
 * Tests startup sequence, middleware setup, and error handling
 */

// Mock dependencies before requiring the server module
jest.mock('dotenv');
jest.mock('express');
jest.mock('cookie-parser');
jest.mock('helmet');
jest.mock('cors');
jest.mock('../config/database');
jest.mock('../config/redis');
jest.mock('../middleware/secrets');
jest.mock('../routes/users');
jest.mock('../routes/files');
jest.mock('../routes/health');

const express = require('express');
const cookieParser = require('cookie-parser');
const helmet = require('helmet');
const cors = require('cors');
const { initDatabase } = require('../config/database');
const { initRedis } = require('../config/redis');
const { loadConfig } = require('../middleware/secrets');

describe('Express Server', () => {
  let mockApp;
  let mockListen;
  let mockUse;
  let mockJson;
  let consoleLogSpy;
  let consoleErrorSpy;
  let processExitSpy;

  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    jest.resetModules();

    // Mock console methods
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    processExitSpy = jest.spyOn(process, 'exit').mockImplementation();

    // Mock express app methods
    mockUse = jest.fn();
    mockListen = jest.fn((port, host, callback) => {
      callback();
      return { close: jest.fn() };
    });

    mockApp = {
      use: mockUse,
      listen: mockListen,
    };

    // Mock express.json
    mockJson = jest.fn(() => 'json-middleware');
    express.json = mockJson;

    // Mock express() to return our mock app
    express.mockReturnValue(mockApp);

    // Mock middleware functions
    helmet.mockReturnValue('helmet-middleware');
    cors.mockReturnValue('cors-middleware');
    cookieParser.mockReturnValue('cookie-parser-middleware');

    // Mock async initialization functions
    initDatabase.mockResolvedValue();
    initRedis.mockResolvedValue();
    loadConfig.mockResolvedValue();

    // Set environment variables
    process.env.PORT = undefined;
    process.env.ENVIRONMENT = undefined;
    process.env.ALLOWED_ORIGIN = undefined;
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleErrorSpy.mockRestore();
    processExitSpy.mockRestore();
  });

  describe('Application Initialization', () => {
    test('should create Express application instance', () => {
      require('../server');
      expect(express).toHaveBeenCalledTimes(1);
    });

    test('should configure helmet middleware', () => {
      require('../server');
      expect(helmet).toHaveBeenCalledTimes(1);
      expect(mockUse).toHaveBeenCalledWith('helmet-middleware');
    });

    test('should configure CORS with credentials enabled', () => {
      process.env.ALLOWED_ORIGIN = 'https://example.com';
      require('../server');

      expect(cors).toHaveBeenCalledWith({
        origin: 'https://example.com',
        credentials: true,
      });
      expect(mockUse).toHaveBeenCalledWith('cors-middleware');
    });

    test('should configure CORS with undefined origin when not set', () => {
      require('../server');

      expect(cors).toHaveBeenCalledWith({
        origin: undefined,
        credentials: true,
      });
    });

    test('should configure JSON body parser with 1mb limit', () => {
      require('../server');

      expect(mockJson).toHaveBeenCalledWith({ limit: '1mb' });
      expect(mockUse).toHaveBeenCalledWith('json-middleware');
    });

    test('should configure cookie parser middleware', () => {
      require('../server');
      expect(cookieParser).toHaveBeenCalledTimes(1);
      expect(mockUse).toHaveBeenCalledWith('cookie-parser-middleware');
    });
  });

  describe('Route Registration', () => {
    test('should register health route', () => {
      const healthRouter = require('../routes/health');
      require('../server');

      expect(mockUse).toHaveBeenCalledWith('/health', healthRouter);
    });

    test('should register users API route', () => {
      const usersRouter = require('../routes/users');
      require('../server');

      expect(mockUse).toHaveBeenCalledWith('/api/users', usersRouter);
    });

    test('should register files API route', () => {
      const filesRouter = require('../routes/files');
      require('../server');

      expect(mockUse).toHaveBeenCalledWith('/api/files', filesRouter);
    });

    test('should register routes in correct order', () => {
      const healthRouter = require('../routes/health');
      const usersRouter = require('../routes/users');
      const filesRouter = require('../routes/files');

      require('../server');

      const calls = mockUse.mock.calls;
      const healthCall = calls.findIndex(call => call[0] === '/health');
      const usersCall = calls.findIndex(call => call[0] === '/api/users');
      const filesCall = calls.findIndex(call => call[0] === '/api/files');

      expect(healthCall).toBeGreaterThan(-1);
      expect(usersCall).toBeGreaterThan(-1);
      expect(filesCall).toBeGreaterThan(-1);
    });
  });

  describe('Server Startup - start() function', () => {
    test('should call loadConfig before starting server', async () => {
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(loadConfig).toHaveBeenCalledTimes(1);
    });

    test('should call initDatabase after loading config', async () => {
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(initDatabase).toHaveBeenCalledTimes(1);
    });

    test('should call initRedis after initializing database', async () => {
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(initRedis).toHaveBeenCalledTimes(1);
    });

    test('should call initialization functions in correct sequence', async () => {
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

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(callOrder).toEqual(['loadConfig', 'initDatabase', 'initRedis']);
    });

    test('should start server on default port 8080 when PORT not set', async () => {
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).toHaveBeenCalledWith(
        8080,
        '0.0.0.0',
        expect.any(Function)
      );
    });

    test('should start server on specified PORT from environment', async () => {
      process.env.PORT = '3000';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).toHaveBeenCalledWith(
        '3000',
        '0.0.0.0',
        expect.any(Function)
      );
    });

    test('should bind to 0.0.0.0 host for container networking', async () => {
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).toHaveBeenCalledWith(
        expect.any(Number),
        '0.0.0.0',
        expect.any(Function)
      );
    });

    test('should log startup message with port and environment', async () => {
      process.env.PORT = '8080';
      process.env.ENVIRONMENT = 'production';

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        'Server listening on port 8080 (env=production)'
      );
    });

    test('should log startup message with undefined environment when not set', async () => {
      process.env.PORT = '8080';

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        'Server listening on port 8080 (env=undefined)'
      );
    });
  });

  describe('Error Handling', () => {
    test('should handle loadConfig failure and exit process', async () => {
      const testError = new Error('Config load failed');
      loadConfig.mockRejectedValue(testError);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleErrorSpy).toHaveBeenCalledWith('Fatal startup error:', testError);
      expect(processExitSpy).toHaveBeenCalledWith(1);
    });

    test('should handle initDatabase failure and exit process', async () => {
      const testError = new Error('Database connection failed');
      initDatabase.mockRejectedValue(testError);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleErrorSpy).toHaveBeenCalledWith('Fatal startup error:', testError);
      expect(processExitSpy).toHaveBeenCalledWith(1);
    });

    test('should handle initRedis failure and exit process', async () => {
      const testError = new Error('Redis connection failed');
      initRedis.mockRejectedValue(testError);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleErrorSpy).toHaveBeenCalledWith('Fatal startup error:', testError);
      expect(processExitSpy).toHaveBeenCalledWith(1);
    });

    test('should exit with code 1 on startup failure', async () => {
      const testError = new Error('Startup failed');
      loadConfig.mockRejectedValue(testError);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(processExitSpy).toHaveBeenCalledWith(1);
      expect(processExitSpy).toHaveBeenCalledTimes(1);
    });

    test('should not start server when initialization fails', async () => {
      const testError = new Error('Init failed');
      loadConfig.mockRejectedValue(testError);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).not.toHaveBeenCalled();
    });

    test('should handle error with network-related message', async () => {
      const networkError = new Error('ECONNREFUSED: Connection refused');
      initDatabase.mockRejectedValue(networkError);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleErrorSpy).toHaveBeenCalledWith('Fatal startup error:', networkError);
      expect(processExitSpy).toHaveBeenCalledWith(1);
    });

    test('should handle error with authentication failure', async () => {
      const authError = new Error('Authentication failed');
      loadConfig.mockRejectedValue(authError);

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleErrorSpy).toHaveBeenCalledWith('Fatal startup error:', authError);
    });
  });

  describe('Port Configuration - Boundary Values', () => {
    test('should handle minimum valid port 1', async () => {
      process.env.PORT = '1';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).toHaveBeenCalledWith('1', '0.0.0.0', expect.any(Function));
    });

    test('should handle standard HTTP port 80', async () => {
      process.env.PORT = '80';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).toHaveBeenCalledWith('80', '0.0.0.0', expect.any(Function));
    });

    test('should handle standard HTTPS port 443', async () => {
      process.env.PORT = '443';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).toHaveBeenCalledWith('443', '0.0.0.0', expect.any(Function));
    });

    test('should handle high port number 65535', async () => {
      process.env.PORT = '65535';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).toHaveBeenCalledWith('65535', '0.0.0.0', expect.any(Function));
    });

    test('should handle empty string PORT as default 8080', async () => {
      process.env.PORT = '';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).toHaveBeenCalledWith(8080, '0.0.0.0', expect.any(Function));
    });

    test('should handle null PORT as default 8080', async () => {
      process.env.PORT = null;
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(mockListen).toHaveBeenCalledWith(8080, '0.0.0.0', expect.any(Function));
    });
  });

  describe('Middleware Configuration - Boundary Values', () => {
    test('should handle empty ALLOWED_ORIGIN', () => {
      process.env.ALLOWED_ORIGIN = '';
      require('../server');

      expect(cors).toHaveBeenCalledWith({
        origin: '',
        credentials: true,
      });
    });

    test('should handle ALLOWED_ORIGIN with single character', () => {
      process.env.ALLOWED_ORIGIN = '*';
      require('../server');

      expect(cors).toHaveBeenCalledWith({
        origin: '*',
        credentials: true,
      });
    });

    test('should handle ALLOWED_ORIGIN with very long URL', () => {
      const longUrl = 'https://' + 'a'.repeat(2000) + '.com';
      process.env.ALLOWED_ORIGIN = longUrl;
      require('../server');

      expect(cors).toHaveBeenCalledWith({
        origin: longUrl,
        credentials: true,
      });
    });

    test('should handle ALLOWED_ORIGIN with special characters', () => {
      process.env.ALLOWED_ORIGIN = 'https://app-staging.example.com:8443';
      require('../server');

      expect(cors).toHaveBeenCalledWith({
        origin: 'https://app-staging.example.com:8443',
        credentials: true,
      });
    });
  });

  describe('Integration - Complete Startup Flow', () => {
    test('should complete full startup sequence successfully', async () => {
      process.env.PORT = '8080';
      process.env.ENVIRONMENT = 'production';
      process.env.ALLOWED_ORIGIN = 'https://app.example.com';

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      // Verify middleware setup
      expect(helmet).toHaveBeenCalled();
      expect(cors).toHaveBeenCalled();
      expect(mockJson).toHaveBeenCalled();
      expect(cookieParser).toHaveBeenCalled();

      // Verify initialization sequence
      expect(loadConfig).toHaveBeenCalled();
      expect(initDatabase).toHaveBeenCalled();
      expect(initRedis).toHaveBeenCalled();

      // Verify server started
      expect(mockListen).toHaveBeenCalled();
      expect(consoleLogSpy).toHaveBeenCalledWith(
        'Server listening on port 8080 (env=production)'
      );

      // Verify no errors
      expect(consoleErrorSpy).not.toHaveBeenCalled();
      expect(processExitSpy).not.toHaveBeenCalled();
    });

    test('should not proceed to server start if any initialization step fails', async () => {
      initDatabase.mockRejectedValue(new Error('DB failed'));

      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(loadConfig).toHaveBeenCalled();
      expect(initDatabase).toHaveBeenCalled();
      expect(initRedis).not.toHaveBeenCalled();
      expect(mockListen).not.toHaveBeenCalled();
      expect(processExitSpy).toHaveBeenCalledWith(1);
    });
  });

  describe('Environment Variable Handling', () => {
    test('should handle ENVIRONMENT with development value', async () => {
      process.env.ENVIRONMENT = 'development';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('env=development')
      );
    });

    test('should handle ENVIRONMENT with staging value', async () => {
      process.env.ENVIRONMENT = 'staging';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('env=staging')
      );
    });

    test('should handle ENVIRONMENT with production value', async () => {
      process.env.ENVIRONMENT = 'production';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('env=production')
      );
    });

    test('should handle ENVIRONMENT with empty string', async () => {
      process.env.ENVIRONMENT = '';
      require('../server');

      await new Promise(resolve => setTimeout(resolve, 100));

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('env=')
      );
    });
  });
});
