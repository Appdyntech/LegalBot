// src/api/customerApi.js
import axios from "axios";

const API_BASE_URL = "${import.meta.env.VITE_API_BASE_URL}/customers";

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

