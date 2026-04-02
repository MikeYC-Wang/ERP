import client from './client'

export const getSummary = () => client.get('/dashboard/summary/')
export const getMonthlyTrend = () => client.get('/dashboard/monthly-trend/')
export const getExpenseBreakdown = () => client.get('/dashboard/expense-breakdown/')
export const getTopProducts = () => client.get('/dashboard/top-products/')
