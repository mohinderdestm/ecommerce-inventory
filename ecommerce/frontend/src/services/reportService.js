import { get } from "../api";

const reportService = {
  getStockSummary: async () => {
    return await get("/reports/stock-summary");
  },

  getLowStock: async () => {
    return await get("/reports/low-stock");
  },

  getTopSelling: async (limit = 10) => {
    return await get(`/reports/top-selling?limit=${limit}`);
  },

  getSupplierPurchases: async () => {
    return await get("/reports/supplier-purchases");
  },

  getDeadStock: async (months = 3) => {
    return await get(`/reports/dead-stock?months=${months}`);
  },

  getMonthlyMovement: async () => {
    return await get("/reports/monthly-movement");
  },
};

export default reportService;
