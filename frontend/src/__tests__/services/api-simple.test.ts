/**
 * Simple API Service Tests
 * Basic tests to validate API service functionality
 */

import { apiService } from '../../services/api';
import { setupFetchMock, mockApiResponses } from '../../setupTests';

describe('API Service Basic Tests', () => {
  test('healthCheck should work', async () => {
    setupFetchMock({
      'GET:/health': mockApiResponses.healthCheck,
    });

    const result = await apiService.healthCheck();
    expect(result.status).toBe('healthy');
  });

  test('sendMessage should work', async () => {
    setupFetchMock({
      'POST:/chat': mockApiResponses.chat,
    });

    const result = await apiService.sendMessage({
      message: 'Test',
      agent_type: 'normal'
    });

    expect(result.response).toBeDefined();
  });
});