import client from './client';

export const getOrders      = ()     => client.get('/orders').then(r => r.data);
export const getOrder       = (id)   => client.get(`/orders/${id}`).then(r => r.data);
export const createOrder    = (data) => client.post('/orders', data).then(r => r.data);
export const deleteOrder    = (id)   => client.delete(`/orders/${id}`);
export const getDashboard   = ()     => client.get('/dashboard/summary').then(r => r.data);
