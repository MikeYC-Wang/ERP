import apiClient from './client'
import type { AxiosResponse } from 'axios'

export function loginApi(data: { username: string; password: string }): Promise<AxiosResponse> {
  return apiClient.post('auth/login/', data)
}

export function registerApi(data: { username: string; email?: string; password: string }): Promise<AxiosResponse> {
  return apiClient.post('auth/register/', data)
}

export function refreshApi(refresh: string): Promise<AxiosResponse> {
  return apiClient.post('auth/refresh/', { refresh })
}

export function getMeApi(): Promise<AxiosResponse> {
  return apiClient.get('auth/me/')
}
