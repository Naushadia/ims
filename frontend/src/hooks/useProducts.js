import { useState, useEffect, useCallback } from 'react';
import * as api from '../api/products';

export function useProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getProducts();
      setProducts(res.data ?? res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refetch(); }, [refetch]);

  const createProduct = async (data) => {
    const product = await api.createProduct(data);
    await refetch();
    return product;
  };

  const updateProduct = async (id, data) => {
    const product = await api.updateProduct(id, data);
    await refetch();
    return product;
  };

  const deleteProduct = async (id) => {
    await api.deleteProduct(id);
    await refetch();
  };

  return { products, loading, error, refetch, createProduct, updateProduct, deleteProduct };
}
