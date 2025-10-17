// web/src/api/customerApi.ts
import axios, { AxiosResponse } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8705/api/v1";
const CUSTOMER_API = `${API_BASE_URL}/customers`;

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
  register: async (data: CustomerRegister): Promise<AxiosResponse<CustomerResponse>> => {
    return await axios.post(`${CUSTOMER_API}/register`, data);
  },

  list: async (): Promise<AxiosResponse<any>> => {
    return await axios.get(CUSTOMER_API);
  },
};

export default customerApi;
