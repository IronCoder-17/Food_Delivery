import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./hooks/AuthContext";
import { CartProvider } from "./hooks/CartContext";
import { AuthorityProvider } from "./hooks/AuthorityContext";
import { ThemeProvider } from "./hooks/ThemeContext";
import ProtectedRoute from "./components/ProtectedRoute";
import CustomerLayout from "./components/CustomerLayout";

import CustomerLogin from "./pages/auth/CustomerLogin";
import CustomerRegister from "./pages/auth/CustomerRegister";
import CompleteProfile from "./pages/auth/CompleteProfile";
import RestaurantLogin from "./pages/auth/RestaurantLogin";
import RestaurantRegister from "./pages/auth/RestaurantRegister";
import AdminLogin from "./pages/auth/AdminLogin";
import { ForgotPassword, ResetPassword } from "./pages/auth/PasswordReset";

import CustomerDashboard from "./pages/customer/CustomerDashboard";
import CartPage from "./pages/customer/CartPage";
import CheckoutPage from "./pages/customer/CheckoutPage";
import OrdersPage from "./pages/customer/OrdersPage";
import WalletPage from "./pages/customer/WalletPage";
import GamePage from "./pages/customer/GamePage";
import ProfilePage from "./pages/customer/ProfilePage";
import AiAssistantPage from "./pages/customer/AiAssistantPage";
import LoyaltyPage from "./pages/customer/LoyaltyPage";
import AddressesPage from "./pages/customer/AddressesPage";
import FavoritesPage from "./pages/customer/FavoritesPage";
import ScheduledOrdersPage from "./pages/customer/ScheduledOrdersPage";
import MealPlannerPage from "./pages/customer/MealPlannerPage";
import GroupOrdersPage from "./pages/customer/GroupOrdersPage";
import ReferralsPage from "./pages/customer/ReferralsPage";
import OrderTrackingPage from "./pages/customer/OrderTrackingPage";
import QuickBitePassPage from "./pages/customer/QuickBitePassPage";
import DisputesPage from "./pages/customer/DisputesPage";
import ChefSpecialsPage from "./pages/customer/ChefSpecialsPage";
import FoodStreakPage from "./pages/customer/FoodStreakPage";
import SurplusDealsPage from "./pages/customer/SurplusDealsPage";
import RecipeToOrderPage from "./pages/customer/RecipeToOrderPage";
import PhotoReorderPage from "./pages/customer/PhotoReorderPage";
import NutritionPage from "./pages/customer/NutritionPage";

import RestaurantLayout from "./pages/restaurant/RestaurantLayout";
import RestaurantDashboardHome from "./pages/restaurant/RestaurantDashboardHome";
import RestaurantFoods from "./pages/restaurant/RestaurantFoods";
import RestaurantCombos from "./pages/restaurant/RestaurantCombos";
import RestaurantFlashSales from "./pages/restaurant/RestaurantFlashSales";
import RestaurantSubscription from "./pages/restaurant/RestaurantSubscription";
import RestaurantOrders from "./pages/restaurant/RestaurantOrders";
import RestaurantProfile from "./pages/restaurant/RestaurantProfile";
import RestaurantKitchenStatus from "./pages/restaurant/RestaurantKitchenStatus";
import RestaurantChefSpecials from "./pages/restaurant/RestaurantChefSpecials";
import RestaurantSurplusDeals from "./pages/restaurant/RestaurantSurplusDeals";

import AdminLayout from "./pages/admin/AdminLayout";
import AdminDashboardHome from "./pages/admin/AdminDashboardHome";
import AdminRestaurants from "./pages/admin/AdminRestaurants";
import AdminCustomers from "./pages/admin/AdminCustomers";
import AdminCategories from "./pages/admin/AdminCategories";
import AdminFoods from "./pages/admin/AdminFoods";
import { AdminOrders, AdminPayments } from "./pages/admin/AdminOrdersPayments";
import AdminGameQuestions from "./pages/admin/AdminGameQuestions";
import AdminLoyalty from "./pages/admin/AdminLoyalty";
import AdminAuthority from "./pages/admin/AdminAuthority";
import AdminFraudCenter from "./pages/admin/AdminFraudCenter";
import AdminPeakHourAnalytics from "./pages/admin/AdminPeakHourAnalytics";
import AdminOrderHeatmap from "./pages/admin/AdminOrderHeatmap";
import AdminPromotions from "./pages/admin/AdminPromotions";
import AdminDisputes from "./pages/admin/AdminDisputes";
import AdminChefSpecials from "./pages/admin/AdminChefSpecials";
import AdminSurplusDeals from "./pages/admin/AdminSurplusDeals";

import "./theme.css";

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AuthorityProvider>
            <CartProvider>
              <Routes>
              {/* ---------------- Public / Customer ---------------- */}
              <Route element={<CustomerLayout />}>
                <Route path="/" element={<ProtectedRoute roles={["customer"]}><CustomerDashboard /></ProtectedRoute>} />
                <Route path="/cart" element={<ProtectedRoute roles={["customer"]}><CartPage /></ProtectedRoute>} />
                <Route path="/checkout" element={<ProtectedRoute roles={["customer"]}><CheckoutPage /></ProtectedRoute>} />
                <Route path="/orders" element={<ProtectedRoute roles={["customer"]}><OrdersPage /></ProtectedRoute>} />
                <Route path="/wallet" element={<ProtectedRoute roles={["customer"]}><WalletPage /></ProtectedRoute>} />
                <Route path="/game" element={<ProtectedRoute roles={["customer"]}><GamePage /></ProtectedRoute>} />
                <Route path="/profile" element={<ProtectedRoute roles={["customer"]}><ProfilePage /></ProtectedRoute>} />
                <Route path="/complete-profile" element={<ProtectedRoute roles={["customer"]} allowIncompleteProfile><CompleteProfile /></ProtectedRoute>} />
                <Route path="/ai-assistant" element={<ProtectedRoute roles={["customer"]}><AiAssistantPage /></ProtectedRoute>} />
                <Route path="/loyalty" element={<ProtectedRoute roles={["customer"]}><LoyaltyPage /></ProtectedRoute>} />
                <Route path="/addresses" element={<ProtectedRoute roles={["customer"]}><AddressesPage /></ProtectedRoute>} />
                <Route path="/favorites" element={<ProtectedRoute roles={["customer"]}><FavoritesPage /></ProtectedRoute>} />
                <Route path="/scheduled-orders" element={<ProtectedRoute roles={["customer"]}><ScheduledOrdersPage /></ProtectedRoute>} />
                <Route path="/meal-planner" element={<ProtectedRoute roles={["customer"]}><MealPlannerPage /></ProtectedRoute>} />
                <Route path="/group-orders" element={<ProtectedRoute roles={["customer"]}><GroupOrdersPage /></ProtectedRoute>} />
                <Route path="/referrals" element={<ProtectedRoute roles={["customer"]}><ReferralsPage /></ProtectedRoute>} />
                <Route path="/orders/:orderId/track" element={<ProtectedRoute roles={["customer"]}><OrderTrackingPage /></ProtectedRoute>} />
                <Route path="/quickbite-pass" element={<ProtectedRoute roles={["customer"]}><QuickBitePassPage /></ProtectedRoute>} />
                <Route path="/disputes" element={<ProtectedRoute roles={["customer"]}><DisputesPage /></ProtectedRoute>} />
                <Route path="/chefs-specials" element={<ProtectedRoute roles={["customer"]}><ChefSpecialsPage /></ProtectedRoute>} />
                <Route path="/food-streak" element={<ProtectedRoute roles={["customer"]}><FoodStreakPage /></ProtectedRoute>} />
                <Route path="/surplus-deals" element={<ProtectedRoute roles={["customer"]}><SurplusDealsPage /></ProtectedRoute>} />
                <Route path="/recipe-to-order" element={<ProtectedRoute roles={["customer"]}><RecipeToOrderPage /></ProtectedRoute>} />
                <Route path="/photo-reorder" element={<ProtectedRoute roles={["customer"]}><PhotoReorderPage /></ProtectedRoute>} />
                <Route path="/nutrition" element={<ProtectedRoute roles={["customer"]}><NutritionPage /></ProtectedRoute>} />

                <Route path="/login" element={<CustomerLogin />} />
                <Route path="/register" element={<CustomerRegister />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />
              </Route>

              {/* ---------------- Restaurant ---------------- */}
              {/* Friendly alias: typing /restaurants directly opens the
                  restaurant portal's login (with a link to the application
                  form), matching what people intuitively try to type. */}
              <Route path="/restaurants" element={<Navigate to="/restaurant/login" replace />} />
              <Route path="/restaurant/login" element={<RestaurantLogin />} />
              <Route path="/restaurant/register" element={<RestaurantRegister />} />
              <Route path="/restaurant" element={<ProtectedRoute roles={["restaurant"]}><RestaurantLayout /></ProtectedRoute>}>
                <Route index element={<RestaurantDashboardHome />} />
                <Route path="foods" element={<RestaurantFoods />} />
                <Route path="combos" element={<RestaurantCombos />} />
                <Route path="flash-sales" element={<RestaurantFlashSales />} />
                <Route path="subscription" element={<RestaurantSubscription />} />
                <Route path="orders" element={<RestaurantOrders />} />
                <Route path="kitchen-status" element={<RestaurantKitchenStatus />} />
                <Route path="chefs-specials" element={<RestaurantChefSpecials />} />
                <Route path="surplus-deals" element={<RestaurantSurplusDeals />} />
                <Route path="profile" element={<RestaurantProfile />} />
              </Route>

              {/* ---------------- Admin ---------------- */}
              <Route path="/admin/login" element={<AdminLogin />} />
              <Route path="/admin" element={<ProtectedRoute roles={["admin"]}><AdminLayout /></ProtectedRoute>}>
                <Route index element={<AdminDashboardHome />} />
                <Route path="restaurants" element={<AdminRestaurants />} />
                <Route path="customers" element={<AdminCustomers />} />
                <Route path="categories" element={<AdminCategories />} />
                <Route path="foods" element={<AdminFoods />} />
                <Route path="orders" element={<AdminOrders />} />
                <Route path="payments" element={<AdminPayments />} />
                <Route path="game-questions" element={<AdminGameQuestions />} />
                <Route path="loyalty" element={<AdminLoyalty />} />
                <Route path="authority" element={<AdminAuthority />} />
                <Route path="fraud" element={<AdminFraudCenter />} />
                <Route path="peak-hours" element={<AdminPeakHourAnalytics />} />
                <Route path="heatmap" element={<AdminOrderHeatmap />} />
                <Route path="promotions" element={<AdminPromotions />} />
                <Route path="disputes" element={<AdminDisputes />} />
                <Route path="chefs-specials" element={<AdminChefSpecials />} />
                <Route path="surplus-deals" element={<AdminSurplusDeals />} />
              </Route>
            </Routes>
            </CartProvider>
          </AuthorityProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}