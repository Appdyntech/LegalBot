// src/api/customerApi.ts
import axios, { AxiosResponse } from "axios";

const API_BASE = "http://127.0.0.1:8705/api/v1/customers";

export interface CustomerRegister {
  name: string;
  email: string;
  phone?: string;
  location?: string;
  google_verified?: boolean;
}

export interface CustomerResponse {
  status: string;
  customer_id: string;
  id: number;
}

const customerApi = {
  register: async (
    data: CustomerRegister
  ): Promise<AxiosResponse<CustomerResponse>> => {
    return await axios.post(`${API_BASE}/register`, data);
  },

  list: async (): Promise<AxiosResponse<any>> => {
    return await axios.get(API_BASE);
  },
};

export default customerApi;
