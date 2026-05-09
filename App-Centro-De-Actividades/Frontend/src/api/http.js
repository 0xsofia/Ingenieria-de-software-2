import axios from "axios";
import router from "@/router";
export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
  withCredentials: true,
});