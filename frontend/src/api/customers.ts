import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface Customer {
  id: number
  name: string
  contact_name: string
  phone: string
  email: string
  address: string
}

export function getCustomers(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('customers/', { params })
}

export function createCustomer(data: Partial<Customer>): Promise<AxiosResponse> {
  return apiClient.post('customers/', data)
}

export function updateCustomer(id: number, data: Partial<Customer>): Promise<AxiosResponse> {
  return apiClient.put(`customers/${id}/`, data)
}

export function deleteCustomer(id: number): Promise<AxiosResponse> {
  return apiClient.delete(`customers/${id}/`)
}
