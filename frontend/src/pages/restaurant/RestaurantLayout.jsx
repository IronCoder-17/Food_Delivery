import { Outlet } from "react-router-dom";
import DashboardLayout from "../../components/DashboardLayout";

const links = [
  { to: "/restaurant", label: "Dashboard", end: true },
  { to: "/restaurant/foods", label: "Food Management" },
  { to: "/restaurant/combos", label: "Combos" },
  { to: "/restaurant/flash-sales", label: "Flash Sales" },
  { to: "/restaurant/subscription", label: "Subscription" },
  { to: "/restaurant/orders", label: "Order Management" },
  { to: "/restaurant/kitchen-status", label: "Kitchen Status" },
  { to: "/restaurant/chefs-specials", label: "Chef's Specials" },
  { to: "/restaurant/surplus-deals", label: "Surplus Deals" },
  { to: "/restaurant/profile", label: "Restaurant Profile" },
];

export default function RestaurantLayout() {
  return (
    <DashboardLayout title="Restaurant" links={links}>
      <Outlet />
    </DashboardLayout>
  );
}
