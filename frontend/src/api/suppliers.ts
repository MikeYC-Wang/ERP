import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface Supplier {
  id: number
  name: string
  contact_name: string
  phone: string
  email: string
  address: string
}

export function getSuppliers(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('suppliers/', { params })
}

export function createSupplier(data: Partial<Supplier>): Promise<AxiosResponse> {
  return apiClient.post('suppliers/', data)
}

export function updateSupplier(id: number, data: Partial<Supplier>): Promise<AxiosResponse> {
  return apiClient.put(`suppliers/${id}/`, data)
}

export function deleteSupplier(id: number): Promise<AxiosResponse> {
  return apiClient.delete(`suppliers/${id}/`)
}
