/**
 * API Service for Junmai AutoDev Mobile Web
 * Handles all API communication with the backend
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5100';

class ApiService {
  constructor() {
    this.baseUrl = API_URL;
  }

  /**
   * Generic fetch wrapper with error handling
   */
  async fetch(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(error.error || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  // System Status APIs
  async getSystemStatus() {
    return this.fetch('/system/status');
  }

  async getSystemHealth() {
    return this.fetch('/system/health');
  }

  async getResourceStatus() {
    return this.fetch('/resource/status');
  }

  // Session APIs
  async getSessions(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = queryString ? `/sessions?${queryString}` : '/sessions';
    return this.fetch(endpoint);
  }

  async getSessionDetail(sessionId) {
    return this.fetch(`/sessions/${sessionId}`);
  }

  async deleteSession(sessionId) {
    return this.fetch(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // Statistics APIs
  async getDailyStatistics(date = null) {
    const endpoint = date ? `/statistics/daily?date=${date}` : '/statistics/daily';
    return this.fetch(endpoint);
  }

  async getWeeklyStatistics() {
    return this.fetch('/statistics/weekly');
  }

  async getMonthlyStatistics() {
    return this.fetch('/statistics/monthly');
  }

  async getPresetStatistics() {
    return this.fetch('/statistics/presets');
  }

  // Approval Queue APIs
  async getApprovalQueue(limit = 100) {
    return this.fetch(`/approval/queue?limit=${limit}`);
  }

  async approvePhoto(photoId) {
    return this.fetch(`/approval/${photoId}/approve`, {
      method: 'POST',
    });
  }

  async rejectPhoto(photoId, reason = '') {
    return this.fetch(`/approval/${photoId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  // Configuration APIs
  async getConfig() {
    return this.fetch('/config');
  }

  async saveConfig(config) {
    return this.fetch('/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async resetConfig() {
    return this.fetch('/config/reset', {
      method: 'POST',
    });
  }

  async validateConfig(config) {
    return this.fetch('/config/validate', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // WebSocket Status
  async getWebSocketStatus() {
    return this.fetch('/websocket/status');
  }

  // Push Notification APIs
  async subscribeToNotifications(subscription) {
    return this.fetch('/notifications/subscribe', {
      method: 'POST',
      body: JSON.stringify(subscription),
    });
  }

  async unsubscribeFromNotifications(endpoint) {
    return this.fetch('/notifications/unsubscribe', {
      method: 'POST',
      body: JSON.stringify({ endpoint }),
    });
  }

  async getNotificationSettings() {
    return this.fetch('/notifications/settings');
  }

  async updateNotificationSettings(settings) {
    return this.fetch('/notifications/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }
}

// Export singleton instance
const apiService = new ApiService();
export default apiService;
