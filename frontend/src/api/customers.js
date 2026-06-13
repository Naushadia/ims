import client from './client';

export const getCustomers    = ()     => client.get('/customers').then(r => r.data);
export const getCustomer     = (id)   => client.get(`/customers/${id}`).then(r => r.data);
export const createCustomer  = (data) => client.post('/customers', data).then(r => r.data);
export const updateCustomer  = (id, data) => client.put(`/customers/${id}`, data).then(r => r.data);
export const deleteCustomer  = (id)   => client.delete(`/customers/${id}`);
