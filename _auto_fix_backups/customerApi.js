// src/api/customerApi.js
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8705/api/v1/customers";

const customerApi = {
  register: async (data) => {
    const res = await axios.post(`${API_BASE_URL}/register`, data);
    return res;
  },

  list: async () => {
    const res = await axios.get(API_BASE_URL);
    return res;
  },
};

export default customerApi;
