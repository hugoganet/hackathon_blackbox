/**
 * HTTP Client Utility for API Communication
 * Provides common HTTP functionality with error handling, timeout, and environment configuration
 */

// Environment variable access that works in both browser and Jest test environments
const getEnvVar = (key: string, fallback: string): string => {
  if (typeof window !== 'undefined' && (window as any).import?.meta?.env) {
    return (window as any).import.meta.env[key] || fallback;
  }
  // Jest test environment fallback
  return fallback;
};

const API_BASE_URL = getEnvVar('VITE_API_BASE_URL', 'http://localhost:8000');
const API_TIMEOUT = parseInt(getEnvVar('VITE_API_TIMEOUT', '30000'));

export interface ApiError {
  message: string;
  status: number;
  statusText: string;
}

export class ApiHttpError extends Error {
  public status: number;
  public statusText: string;

  constructor(message: string, status: number, statusText: string) {
    super(message);
    this.name = 'ApiHttpError';
    this.status = status;
    this.statusText = statusText;
  }
}

/**
 * HTTP Client with timeout and error handling
 */
export class HttpClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = API_BASE_URL, timeout: number = API_TIMEOUT) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = timeout;
  }

  /**
   * Create fetch request with timeout
   */
  private async fetchWithTimeout(url: string, options: RequestInit): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiHttpError('Request timeout', 408, 'Request Timeout');
      }
      throw error;
    }
  }

  /**
   * Handle HTTP response and errors
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } catch {
        // Keep default error message if JSON parsing fails
      }

      throw new ApiHttpError(errorMessage, response.status, response.statusText);
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }

    return response.text() as unknown as T;
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, params?: Record<string, string | number | boolean>): Promise<T> {
    let url = `${this.baseUrl}${endpoint}`;
    
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, String(value));
      });
      url += `?${searchParams.toString()}`;
    }

    const response = await this.fetchWithTimeout(url, {
      method: 'GET',
    });

    return this.handleResponse<T>(response);
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await this.fetchWithTimeout(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, params?: Record<string, string | number | boolean>): Promise<T> {
    let url = `${this.baseUrl}${endpoint}`;
    
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        searchParams.append(key, String(value));
      });
      url += `?${searchParams.toString()}`;
    }

    const response = await this.fetchWithTimeout(url, {
      method: 'DELETE',
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Health check to verify API connectivity
   */
  async healthCheck(): Promise<{ status: string; message: string }> {
    return this.get<{ status: string; message: string }>('/health');
  }
}

// Default HTTP client instance
export const httpClient = new HttpClient();

// Environment configuration
export const getDefaultUserId = (): string => {
  return getEnvVar('VITE_DEFAULT_USER_ID', 'user123');
};

export { API_BASE_URL, API_TIMEOUT };