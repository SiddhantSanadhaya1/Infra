/**
 * Unit tests for API service
 */
import axios from 'axios';
import { api } from '../api';


// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;


describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Health Endpoint', () => {
    it('calls health check endpoint', async () => {
      const mockResponse = { data: { status: 'healthy' } };
      mockedAxios.create = jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue(mockResponse),
      } as any);

      const { api: testApi } = require('../api');
      const result = await testApi.health();

      expect(result).toEqual({ status: 'healthy' });
    });
  });

  describe('Policyholder Endpoints', () => {
    beforeEach(() => {
      mockedAxios.create = jest.fn().mockReturnValue({
        post: jest.fn().mockResolvedValue({ data: {} }),
        get: jest.fn().mockResolvedValue({ data: {} }),
        put: jest.fn().mockResolvedValue({ data: {} }),
      } as any);
    });

    it('creates policyholder with correct data', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { id: 'ph-123', email: 'test@example.com' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const data = { first_name: 'John', last_name: 'Doe', email: 'test@example.com' };
      const result = await testApi.createPolicyholder(data);

      expect(mockClient.post).toHaveBeenCalledWith('/api/policyholders', data);
      expect(result.email).toBe('test@example.com');
    });

    it('gets policyholder by ID', async () => {
      const mockClient = {
        get: jest.fn().mockResolvedValue({
          data: { id: 'ph-456', email: 'jane@example.com' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const result = await testApi.getPolicyholder('ph-456');

      expect(mockClient.get).toHaveBeenCalledWith('/api/policyholders/ph-456');
      expect(result.id).toBe('ph-456');
    });

    it('lists policyholders with pagination params', async () => {
      const mockClient = {
        get: jest.fn().mockResolvedValue({ data: [] }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      await testApi.listPolicyholders({ skip: 10, limit: 20 });

      expect(mockClient.get).toHaveBeenCalledWith('/api/policyholders', {
        params: { skip: 10, limit: 20 },
      });
    });

    it('updates policyholder', async () => {
      const mockClient = {
        put: jest.fn().mockResolvedValue({
          data: { id: 'ph-789', phone: '555-1234' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const updateData = { phone: '555-1234' };
      const result = await testApi.updatePolicyholder('ph-789', updateData);

      expect(mockClient.put).toHaveBeenCalledWith('/api/policyholders/ph-789', updateData);
      expect(result.phone).toBe('555-1234');
    });
  });

  describe('Policy Endpoints', () => {
    beforeEach(() => {
      mockedAxios.create = jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue({ data: [] }),
        post: jest.fn().mockResolvedValue({ data: {} }),
        put: jest.fn().mockResolvedValue({ data: {} }),
      } as any);
    });

    it('gets policies with filter params', async () => {
      const mockClient = {
        get: jest.fn().mockResolvedValue({ data: [] }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      await testApi.getPolicies({ status: 'ACTIVE', policy_type: 'AUTO' });

      expect(mockClient.get).toHaveBeenCalledWith('/api/policies', {
        params: { status: 'ACTIVE', policy_type: 'AUTO' },
      });
    });

    it('gets single policy by ID', async () => {
      const mockClient = {
        get: jest.fn().mockResolvedValue({
          data: { id: 'pol-123', policy_number: 'POL-AUTO-123' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const result = await testApi.getPolicy('pol-123');

      expect(mockClient.get).toHaveBeenCalledWith('/api/policies/pol-123');
      expect(result.policy_number).toBe('POL-AUTO-123');
    });

    it('creates policy', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { id: 'pol-456', status: 'ACTIVE' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const policyData = { policyholder_id: 'ph-123', policy_type: 'HOME' };
      const result = await testApi.createPolicy(policyData);

      expect(mockClient.post).toHaveBeenCalledWith('/api/policies', policyData);
      expect(result.status).toBe('ACTIVE');
    });

    it('updates policy', async () => {
      const mockClient = {
        put: jest.fn().mockResolvedValue({
          data: { id: 'pol-789', status: 'CANCELLED' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const updateData = { status: 'CANCELLED' };
      const result = await testApi.updatePolicy('pol-789', updateData);

      expect(mockClient.put).toHaveBeenCalledWith('/api/policies/pol-789', updateData);
      expect(result.status).toBe('CANCELLED');
    });

    it('gets policy documents', async () => {
      const mockClient = {
        get: jest.fn().mockResolvedValue({ data: [{ id: 'doc-1' }, { id: 'doc-2' }] }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const result = await testApi.getPolicyDocuments('pol-123');

      expect(mockClient.get).toHaveBeenCalledWith('/api/policies/pol-123/documents');
      expect(result).toHaveLength(2);
    });
  });

  describe('Claim Endpoints', () => {
    beforeEach(() => {
      mockedAxios.create = jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue({ data: [] }),
        post: jest.fn().mockResolvedValue({ data: {} }),
        put: jest.fn().mockResolvedValue({ data: {} }),
      } as any);
    });

    it('gets claims with filter params', async () => {
      const mockClient = {
        get: jest.fn().mockResolvedValue({ data: [] }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      await testApi.getClaims({ status: 'SUBMITTED', policy_id: 'pol-123' });

      expect(mockClient.get).toHaveBeenCalledWith('/api/claims', {
        params: { status: 'SUBMITTED', policy_id: 'pol-123' },
      });
    });

    it('gets single claim by ID', async () => {
      const mockClient = {
        get: jest.fn().mockResolvedValue({
          data: { id: 'claim-123', status: 'APPROVED' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const result = await testApi.getClaim('claim-123');

      expect(mockClient.get).toHaveBeenCalledWith('/api/claims/claim-123');
      expect(result.status).toBe('APPROVED');
    });

    it('creates claim', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { id: 'claim-456', status: 'SUBMITTED' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const claimData = {
        policy_id: 'pol-123',
        incident_date: '2026-03-15',
        claim_type: 'COLLISION',
        description: 'Car accident',
        amount_requested: 5000,
      };
      const result = await testApi.createClaim(claimData);

      expect(mockClient.post).toHaveBeenCalledWith('/api/claims', claimData);
      expect(result.status).toBe('SUBMITTED');
    });

    it('updates claim', async () => {
      const mockClient = {
        put: jest.fn().mockResolvedValue({
          data: { id: 'claim-789', status: 'UNDER_REVIEW' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const updateData = { status: 'UNDER_REVIEW' };
      const result = await testApi.updateClaim('claim-789', updateData);

      expect(mockClient.put).toHaveBeenCalledWith('/api/claims/claim-789', updateData);
      expect(result.status).toBe('UNDER_REVIEW');
    });

    it('approves claim', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { id: 'claim-111', status: 'APPROVED', amount_approved: 4500 },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const result = await testApi.approveClaim('claim-111', 4500, 'Approved');

      expect(mockClient.post).toHaveBeenCalledWith('/api/claims/claim-111/approve', {
        amount_approved: 4500,
        notes: 'Approved',
      });
      expect(result.amount_approved).toBe(4500);
    });

    it('rejects claim', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { id: 'claim-222', status: 'REJECTED' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const result = await testApi.rejectClaim('claim-222', 'Insufficient evidence');

      expect(mockClient.post).toHaveBeenCalledWith('/api/claims/claim-222/reject', {
        reason: 'Insufficient evidence',
      });
      expect(result.status).toBe('REJECTED');
    });
  });

  describe('Document Endpoints', () => {
    beforeEach(() => {
      mockedAxios.create = jest.fn().mockReturnValue({
        post: jest.fn().mockResolvedValue({ data: {} }),
        get: jest.fn().mockResolvedValue({ data: {} }),
      } as any);
    });

    it('gets presigned upload URL', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { upload_url: 'https://s3.url', file_key: 'key123' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const requestData = {
        file_name: 'doc.pdf',
        document_type: 'POLICY',
        content_type: 'application/pdf',
      };
      const result = await testApi.presignDocument(requestData);

      expect(mockClient.post).toHaveBeenCalledWith('/api/documents/presign', requestData);
      expect(result.upload_url).toBe('https://s3.url');
      expect(result.file_key).toBe('key123');
    });

    it('registers document', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { id: 'doc-123', file_name: 'test.pdf' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const docData = {
        file_key: 'key456',
        file_name: 'test.pdf',
        document_type: 'CLAIM',
        claim_id: 'claim-789',
      };
      const result = await testApi.registerDocument(docData);

      expect(mockClient.post).toHaveBeenCalledWith('/api/documents', docData);
      expect(result.file_name).toBe('test.pdf');
    });

    it('gets document download URL', async () => {
      const mockClient = {
        get: jest.fn().mockResolvedValue({
          data: { download_url: 'https://s3.download', file_name: 'doc.pdf' },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const result = await testApi.getDocumentDownloadUrl('doc-123');

      expect(mockClient.get).toHaveBeenCalledWith('/api/documents/doc-123');
      expect(result.download_url).toBe('https://s3.download');
    });
  });

  describe('Quote Endpoints', () => {
    beforeEach(() => {
      mockedAxios.create = jest.fn().mockReturnValue({
        post: jest.fn().mockResolvedValue({ data: {} }),
      } as any);
    });

    it('gets auto insurance quote', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { premium_monthly: 150, premium_annual: 1800 },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const quoteData = {
        driver_age: 30,
        vehicle_year: 2020,
        coverage_type: 'COMPREHENSIVE',
        annual_mileage: 12000,
      };
      const result = await testApi.quoteAuto(quoteData);

      expect(mockClient.post).toHaveBeenCalledWith('/api/quotes/auto', quoteData);
      expect(result.premium_annual).toBe(1800);
    });

    it('gets home insurance quote', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { premium_monthly: 200, premium_annual: 2400 },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const quoteData = {
        home_value: 300000,
        location_risk: 'MEDIUM',
        home_age_years: 10,
        coverage_type: 'STANDARD',
      };
      const result = await testApi.quoteHome(quoteData);

      expect(mockClient.post).toHaveBeenCalledWith('/api/quotes/home', quoteData);
      expect(result.premium_annual).toBe(2400);
    });

    it('gets life insurance quote', async () => {
      const mockClient = {
        post: jest.fn().mockResolvedValue({
          data: { premium_monthly: 75, premium_annual: 900 },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');
      const quoteData = {
        age: 35,
        health_score: 85,
        coverage_amount: 500000,
        term_years: 20,
      };
      const result = await testApi.quoteLife(quoteData);

      expect(mockClient.post).toHaveBeenCalledWith('/api/quotes/life', quoteData);
      expect(result.premium_annual).toBe(900);
    });
  });

  describe('Error Handling', () => {
    it('throws error when request fails', async () => {
      const mockClient = {
        get: jest.fn().mockRejectedValue(new Error('Network error')),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');

      await expect(testApi.health()).rejects.toThrow('Network error');
    });

    it('handles 404 errors', async () => {
      const mockClient = {
        get: jest.fn().mockRejectedValue({
          response: { status: 404, data: { detail: 'Not found' } },
        }),
      };
      mockedAxios.create = jest.fn().mockReturnValue(mockClient as any);

      const { api: testApi } = require('../api');

      await expect(testApi.getPolicy('nonexistent')).rejects.toMatchObject({
        response: { status: 404 },
      });
    });
  });
});
