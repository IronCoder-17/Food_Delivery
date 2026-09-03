import { Outlet } from "react-router-dom";
import DashboardLayout from "../../components/DashboardLayout";

const links = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/restaurants", label: "Restaurants" },
  { to: "/admin/customers", label: "Customers" },
  { to: "/admin/categories", label: "Categories" },
  { to: "/admin/foods", label: "Food Items" },
  { to: "/admin/orders", label: "Orders" },
  { to: "/admin/payments", label: "Payments" },
  { to: "/admin/game-questions", label: "GK Questions" },
  { to: "/admin/loyalty", label: "Loyalty Management" },
  { to: "/admin/authority", label: "Authority Management" },
  { to: "/admin/fraud", label: "Fraud & Risk Center" },
  { to: "/admin/peak-hours", label: "Peak-Hour Analytics" },
  { to: "/admin/heatmap", label: "Order Heatmap" },
  { to: "/admin/promotions", label: "Promotion Experiments" },
  { to: "/admin/disputes", label: "Disputes" },
  { to: "/admin/chefs-specials", label: "Chef's Specials" },
  { to: "/admin/surplus-deals", label: "Surplus Deals" },
];

export default function AdminLayout() {
  return (
    <DashboardLayout title="Admin Panel" links={links}>
      <Outlet />
    </DashboardLayout>
  );
}
