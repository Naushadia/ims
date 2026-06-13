import { useState, useEffect, useCallback } from 'react';
import * as api from '../api/customers';

export function useCustomers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getCustomers();
      setCustomers(res.data ?? res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refetch(); }, [refetch]);

  const createCustomer = async (data) => {
    const customer = await api.createCustomer(data);
    await refetch();
    return customer;
  };

  const updateCustomer = async (id, data) => {
    const customer = await api.updateCustomer(id, data);
    await refetch();
    return customer;
  };

  const deleteCustomer = async (id) => {
    await api.deleteCustomer(id);
    await refetch();
  };

  return { customers, loading, error, refetch, createCustomer, updateCustomer, deleteCustomer };
}
