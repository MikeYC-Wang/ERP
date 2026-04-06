import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface OrderItem {
  product: number
  product_name: string
  quantity: number
  unit_price: number
  subtotal: number
}

export interface Order {
  id?: number
  order_number?: string
  customer_name?: string
  customer_ref?: number | null
  order_date?: string
  date?: string
  status?: 'pending' | 'shipped' | 'completed' | string
  total_amount?: number
  items?: OrderItem[]
}

export function getOrders(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('orders/', { params })
}

export function createOrder(data: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.post('orders/', data)
}

export function shipOrder(id: number): Promise<AxiosResponse> {
  return apiClient.post(`orders/${id}/ship/`)
}

export function completeOrder(id: number): Promise<AxiosResponse> {
  return apiClient.post(`orders/${id}/complete/`)
}
