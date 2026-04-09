import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface ProductPackaging {
  id?: number
  name: string
  quantity: number
  price: number
  cost: number
  barcode?: string
  is_default: boolean
}

export interface Product {
  id: number
  sku: string
  name: string
  unit: string
  base_unit?: string
  current_price: number
  last_cost?: number
  safety_stock?: number
  supplier?: number | null
  supplier_name?: string
  category?: number | null
  category_name?: string
  packagings?: ProductPackaging[]
}

export interface Category {
  id: number
  name: string
  parent: number | null
  parent_name?: string
  full_name?: string
  children_count?: number
  depth?: number
}

export function getCategories(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('categories/', { params })
}

export function getCategoryTree(): Promise<AxiosResponse> {
  return apiClient.get('categories/tree/')
}

export function getCategory(id: number): Promise<AxiosResponse> {
  return apiClient.get(`categories/${id}/`)
}

export function createCategory(payload: Partial<Category>): Promise<AxiosResponse> {
  return apiClient.post('categories/', payload)
}

export function updateCategory(id: number, payload: Partial<Category>): Promise<AxiosResponse> {
  return apiClient.put(`categories/${id}/`, payload)
}

export function deleteCategory(id: number): Promise<AxiosResponse> {
  return apiClient.delete(`categories/${id}/`)
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
  packaging?: number | null
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

export interface BulkImportRow {
  sku: string
  name: string
  barcode?: string
  base_unit?: string
  safety_stock?: number
  packagings: ProductPackaging[]
}

export interface BulkImportPayload {
  supplier: number | null
  category?: number | null
  rows: BulkImportRow[]
}

export function bulkImportProducts(payload: BulkImportPayload): Promise<AxiosResponse> {
  return apiClient.post('products/bulk-import/', payload)
}

export function parseProductsXlsx(file: File): Promise<AxiosResponse> {
  const fd = new FormData()
  fd.append('file', file)
  return apiClient.post('products/parse-xlsx/', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
