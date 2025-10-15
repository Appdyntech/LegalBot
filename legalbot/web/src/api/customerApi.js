// src/api/customerApi.js
import axios from "axios";

const API_BASE = "http://127.0.0.1:8705/api/v1/customers";

const customerApi = {
  register: async (data) => {
    const res = await axios.post(`${API_BASE}/register`, data);
    return res;
  },

  list: async () => {
    const res = await axios.get(API_BASE);
    return res;
  },
};

export default customerApi;
