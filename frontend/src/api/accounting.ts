import apiClient from './client'
import type { AxiosResponse } from 'axios'

export interface AccountSubject {
  id: number
  code: string
  name: string
  category: string
}

export interface JournalVoucherEntry {
  account_subject: number
  debit_amount: number
  credit_amount: number
}

export interface JournalVoucher {
  id: number
  date: string
  voucher_number: string
  description: string
  is_system_generated: boolean
  entries: JournalVoucherEntry[]
}

export function getAccountSubjects(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('account-subjects/', { params })
}

export function createAccountSubject(data: Partial<AccountSubject>): Promise<AxiosResponse> {
  return apiClient.post('account-subjects/', data)
}

export function updateAccountSubject(id: number, data: Partial<AccountSubject>): Promise<AxiosResponse> {
  return apiClient.put(`account-subjects/${id}/`, data)
}

export function deleteAccountSubject(id: number): Promise<AxiosResponse> {
  return apiClient.delete(`account-subjects/${id}/`)
}

export function getJournalVouchers(params?: Record<string, unknown>): Promise<AxiosResponse> {
  return apiClient.get('journal-vouchers/', { params })
}

export function createJournalVoucher(data: Partial<JournalVoucher>): Promise<AxiosResponse> {
  return apiClient.post('journal-vouchers/', data)
}
