import axios from 'axios';

const API_BASE_URLS = {
  routing: 'http://localhost:8000/api/v1',
  telemetry: 'http://localhost:8001/api/v1',
  sharedMobility: 'http://localhost:8002',
  payment: 'http://localhost:3000',
  audit: 'http://localhost:8003/api/v1',
};

export const routingService = {
  getStops: () => axios.get(`${API_BASE_URLS.routing}/stops`),
  planRoute: (data: any) => axios.post(`${API_BASE_URLS.routing}/routes`, data),
};

export const sharedMobilityService = {
  getVehicles: () => axios.get(`${API_BASE_URLS.sharedMobility}/vehicles`),
  createReservation: (data: any) => axios.post(`${API_BASE_URLS.sharedMobility}/reservations`, data),
};

export const paymentService = {
  getUserTransactions: (userId: string) => axios.get(`${API_BASE_URLS.payment}/users/${userId}/transactions`),
  processPayment: (data: any) => axios.post(`${API_BASE_URLS.payment}/payments/tap`, data),
  createUser: (data: any) => axios.post(`${API_BASE_URLS.payment}/users`, data),
};

export const auditService = {
  getLogs: () => axios.get(`${API_BASE_URLS.audit}/logs`),
};