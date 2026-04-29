import React, { useState, useEffect } from "react";
import reportService from "../services/reportService";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";

const ReportsAnalytics = () => {
  const [activeTab, setActiveTab] = useState("stockSummary");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const tabs = [
    { id: "stockSummary", label: "Stock Summary by Warehouse" },
    { id: "lowStock", label: "Low-Stock Report" },
    { id: "topSelling", label: "Top-Selling Products" },
    { id: "supplierPurchases", label: "Supplier-wise Purchases" },
    { id: "deadStock", label: "Dead Stock Report" },
    { id: "monthlyMovement", label: "Monthly Movement" },
  ];

  const fetchData = async () => {
    setLoading(true);
    setError("");
    setData([]);
    try {
      let result = [];
      switch (activeTab) {
        case "stockSummary":
          result = await reportService.getStockSummary();
          break;
        case "lowStock":
          result = await reportService.getLowStock();
          break;
        case "topSelling":
          result = await reportService.getTopSelling(10);
          break;
        case "supplierPurchases":
          result = await reportService.getSupplierPurchases();
          break;
        case "deadStock":
          result = await reportService.getDeadStock(3);
          break;
        case "monthlyMovement":
          result = await reportService.getMonthlyMovement();
          break;
        default:
          break;
      }
      setData(result);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch report data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const getReportContent = () => {
    let head = [];
    let body = [];

    switch (activeTab) {
      case "stockSummary":
        head = [["Warehouse Name", "Product Count", "Total Quantity"]];
        body = data.map((row) => [
          row.warehouse_name,
          row.product_count,
          row.total_quantity,
        ]);
        break;
      case "lowStock":
        head = [["Product Name", "SKU", "Total Stock", "Reorder Level", "Shortfall"]];
        body = data.map((row) => [
          row.product_name,
          row.sku,
          row.total_stock,
          row.reorder_level,
          row.shortfall,
        ]);
        break;
      case "topSelling":
        head = [["Product Name", "SKU", "Total Sold", "Total Revenue"]];
        body = data.map((row) => [
          row.product_name,
          row.sku,
          row.total_quantity_sold,
          `₹${row.total_revenue.toFixed(2)}`,
        ]);
        break;
      case "supplierPurchases":
        head = [["Supplier Name", "Total Orders", "Total Value"]];
        body = data.map((row) => [
          row.supplier_name,
          row.total_orders,
          `₹${row.total_purchased_value.toFixed(2)}`,
        ]);
        break;
      case "deadStock":
        head = [["Product Name", "SKU", "Total Stock", "Dead Stock Value"]];
        body = data.map((row) => [
          row.product_name,
          row.sku,
          row.total_stock,
          `₹${row.dead_stock_value.toFixed(2)}`,
        ]);
        break;
      case "monthlyMovement":
        head = [["Month/Year", "Total Inward", "Total Outward", "Net Movement"]];
        body = data.map((row) => [
          `${row.month}/${row.year}`,
          row.total_inward,
          row.total_outward,
          row.net_movement,
        ]);
        break;
      default:
        break;
    }
    return { head, body };
  };

  const generatePDF = () => {
    if (data.length === 0) return;
    const doc = new jsPDF();
    const currentTab = tabs.find((t) => t.id === activeTab);

    doc.text(currentTab.label, 14, 15);
    const { head, body } = getReportContent();

    autoTable(doc, {
      head: head,
      body: body,
      startY: 20,
      theme: "grid",
    });

    doc.save(`${activeTab}_report.pdf`);
  };

  const generateExcel = () => {
    if (data.length === 0) return;
    const { head, body } = getReportContent();
    const ws_data = [head[0], ...body];
    const ws = XLSX.utils.aoa_to_sheet(ws_data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Report");
    XLSX.writeFile(wb, `${activeTab}_report.xlsx`);
  };

  const renderTableHead = () => {
    switch (activeTab) {
      case "stockSummary":
        return (
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Warehouse Name</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Count</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Quantity</th>
          </tr>
        );
      case "lowStock":
        return (
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Name</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Stock</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reorder Level</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Shortfall</th>
          </tr>
        );
      case "topSelling":
        return (
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Name</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Sold</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Revenue</th>
          </tr>
        );
      case "supplierPurchases":
        return (
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Supplier Name</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Orders</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Value</th>
          </tr>
        );
      case "deadStock":
        return (
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product Name</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Stock</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dead Stock Value</th>
          </tr>
        );
      case "monthlyMovement":
        return (
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Month/Year</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Inward</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Outward</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Net Movement</th>
          </tr>
        );
      default:
        return null;
    }
  };

  const renderTableRow = (row, index) => {
    switch (activeTab) {
      case "stockSummary":
        return (
          <tr key={index} className="hover:bg-gray-50">
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.warehouse_name}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.product_count}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.total_quantity}</td>
          </tr>
        );
      case "lowStock":
        return (
          <tr key={index} className="hover:bg-gray-50">
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.product_name}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.sku}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600">{row.total_stock}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.reorder_level}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.shortfall}</td>
          </tr>
        );
      case "topSelling":
        return (
          <tr key={index} className="hover:bg-gray-50">
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.product_name}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.sku}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.total_quantity_sold}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₹{row.total_revenue?.toFixed(2)}</td>
          </tr>
        );
      case "supplierPurchases":
        return (
          <tr key={index} className="hover:bg-gray-50">
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.supplier_name}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.total_orders}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₹{row.total_purchased_value?.toFixed(2)}</td>
          </tr>
        );
      case "deadStock":
        return (
          <tr key={index} className="hover:bg-gray-50">
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.product_name}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.sku}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.total_stock}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₹{row.dead_stock_value?.toFixed(2)}</td>
          </tr>
        );
      case "monthlyMovement":
        return (
          <tr key={index} className="hover:bg-gray-50">
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{row.month}/{row.year}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">+{row.total_inward}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">-{row.total_outward}</td>
            <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold">{row.net_movement}</td>
          </tr>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Reports and Analytics</h1>
        <div className="space-x-3">
          <button
            onClick={generateExcel}
            disabled={loading || data.length === 0}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none disabled:opacity-50"
          >
            Export as Excel
          </button>
          <button
            onClick={generatePDF}
            disabled={loading || data.length === 0}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none disabled:opacity-50"
          >
            Export as PDF
          </button>
        </div>
      </div>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`${activeTab === tab.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {error && (
        <div className="bg-red-50 p-4 rounded-md">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              {renderTableHead()}
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                    Loading data...
                  </td>
                </tr>
              ) : data.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500">
                    No data available for this report.
                  </td>
                </tr>
              ) : (
                data.map((row, index) => renderTableRow(row, index))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ReportsAnalytics;
