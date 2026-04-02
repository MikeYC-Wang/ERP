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
  id: number
  order_number: string
  customer_name: string
  date: string
  status: 'pending' | 'shipped' | 'completed'
  total_amount: number
  items: OrderItem[]
}

export function getOrders(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('orders/', { params })
}

export function createOrder(data: Partial<Order>): Promise<AxiosResponse> {
  return apiClient.post('orders/', data)
}

export function completeOrder(id: number): Promise<AxiosResponse> {
  return apiClient.post(`orders/${id}/complete/`)
}
