import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface Product {
  id: number
  sku: string
  name: string
  unit: string
  current_price: number
  safety_stock?: number
}

export interface InventoryBatch {
  id: number
  product: number
  product_name: string
  batch_number: string
  quantity: number
  remaining_quantity: number
  unit_cost: number
  received_date: string
}

export interface PurchaseOrderItem {
  id?: number
  product: number
  quantity: number
  fee: number
}

export interface PurchaseOrder {
  id: number
  order_number: string
  supplier: string
  date: string
  status: string
  items: PurchaseOrderItem[]
}

export function getProducts(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('products/', { params })
}

export function createProduct(data: Partial<Product>): Promise<AxiosResponse> {
  return apiClient.post('products/', data)
}

export function updateProduct(id: number, data: Partial<Product>): Promise<AxiosResponse> {
  return apiClient.put(`products/${id}/`, data)
}

export function deleteProduct(id: number): Promise<AxiosResponse> {
  return apiClient.delete(`products/${id}/`)
}

export function getInventoryBatches(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('inventory-batches/', { params })
}

export function getPurchaseOrders(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('purchase-orders/', { params })
}

export function createPurchaseOrder(data: Partial<PurchaseOrder>): Promise<AxiosResponse> {
  return apiClient.post('purchase-orders/', data)
}

export function receivePurchaseOrder(id: number): Promise<AxiosResponse> {
  return apiClient.post(`purchase-orders/${id}/receive/`)
}

export function updatePurchaseOrder(id: number, data: Partial<PurchaseOrder>): Promise<AxiosResponse> {
  return apiClient.put(`purchase-orders/${id}/`, data)
}

export function deletePurchaseOrder(id: number): Promise<AxiosResponse> {
  return apiClient.delete(`purchase-orders/${id}/`)
}

export function getStockSummary(): Promise<AxiosResponse> {
  return apiClient.get('inventory/stock-summary/')
}
