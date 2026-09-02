import api from "./api";

// ---------------- Auth ----------------
export const sendOtp = (mobile_number) => api.post("/auth/otp/send", { mobile_number });
export const verifyOtp = (mobile_number, otp_code) => api.post("/auth/otp/verify", { mobile_number, otp_code });

export const customerRegister = (payload) => api.post("/auth/customer/register", payload);
export const customerLogin = (email, password) => api.post("/auth/customer/login", { email, password });
export const customerGoogleLogin = (credential) => api.post("/auth/customer/google", { credential });
export const completeGoogleProfile = (payload) => api.post("/customer/complete-profile", payload);

export const restaurantRegister = (payload) => api.post("/auth/restaurant/register", payload);
export const restaurantLogin = (email, password) => api.post("/auth/restaurant/login", { email, password });

export const adminLogin = (email, password) => api.post("/auth/admin/login", { email, password });

export const forgotPassword = (email) => api.post("/auth/forgot-password", { email });
export const resetPassword = (payload) => api.post("/auth/reset-password", payload);

// ---------------- Locations ----------------
export const getStates = () => api.get("/locations/states");
export const getCities = (stateId) => api.get(`/locations/states/${stateId}/cities`);

// ---------------- Food / Categories ----------------
export const getCategories = () => api.get("/foods/categories");
export const getFoods = (params) => api.get("/foods", { params });
export const getFood = (id) => api.get(`/foods/${id}`);
export const getRestaurantsPublic = (params) => api.get("/foods/restaurants", { params });

// ---------------- Cart ----------------
export const getCart = () => api.get("/cart");
export const addToCart = (food_id, quantity = 1) => api.post("/cart/add", { food_id, quantity });
export const updateCartItem = (cart_item_id, quantity) => api.put("/cart/update", { cart_item_id, quantity });
export const removeCartItem = (id) => api.delete(`/cart/remove/${id}`);
export const clearCart = () => api.delete("/cart/clear");

// ---------------- Orders ----------------
export const createOrder = (payload) => api.post("/orders", payload);
export const getMyOrders = () => api.get("/orders/mine");
export const getRestaurantOrders = () => api.get("/orders/restaurant");
export const getOrder = (id) => api.get(`/orders/${id}`);
export const updateOrderStatus = (id, status) => api.put(`/orders/${id}/status`, { status });

// ---------------- Payments ----------------
export const createRazorpayOrder = (order_id) => api.post("/payments/razorpay/create-order", { order_id });
export const verifyRazorpayPayment = (payload) => api.post("/payments/razorpay/verify", payload);

// ---------------- Wallet ----------------
export const getWallet = () => api.get("/wallet");
export const getWalletTransactions = () => api.get("/wallet/transactions");

// ---------------- Game ----------------
export const startGame = () => api.post("/game/start");
export const submitAnswer = (payload) => api.post("/game/answer", payload);
export const finishGame = (session_id) => api.post("/game/finish", { session_id });
export const getGameHistory = () => api.get("/game/history");

// ---------------- Restaurant self-service ----------------
export const getRestaurantProfile = () => api.get("/restaurant/profile");
export const updateRestaurantProfile = (payload) => api.put("/restaurant/profile", payload);
export const getRestaurantDashboard = () => api.get("/restaurant/dashboard");
export const getRestaurantAnalytics = () => api.get("/restaurant/analytics");
export const getOwnFoods = () => api.get("/restaurant/foods");
export const addFood = (payload) => api.post("/restaurant/foods", payload);
export const updateFood = (id, payload) => api.put(`/restaurant/foods/${id}`, payload);
export const deleteFood = (id) => api.delete(`/restaurant/foods/${id}`);

// ---------------- Customer self-service ----------------
export const getCustomerProfile = () => api.get("/customer/profile");
export const updateCustomerProfile = (payload) => api.put("/customer/profile", payload);

// ---------------- Customer authorities (self) ----------------
export const getMyAuthorities = () => api.get("/customer/authorities");
export const getMyRestaurantAuthorities = () => api.get("/restaurant/authorities");

// ---------------- AI Assistant ----------------
export const askAiAssistant = (message, history) => api.post("/customer/ai-assistant", { message, history });

// ---------------- Loyalty (customer) ----------------
export const getMyLoyalty = () => api.get("/customer/loyalty");
export const getMyLoyaltyTransactions = () => api.get("/customer/loyalty/transactions");
export const getLoyaltyLevelsPublic = () => api.get("/customer/loyalty/levels");

// ---------------- Orders: cancel ----------------
export const cancelOrder = (id) => api.put(`/orders/${id}/cancel`);

// ---------------- Saved Addresses ----------------
export const getAddresses = () => api.get("/customer/addresses");
export const addAddress = (payload) => api.post("/customer/addresses", payload);
export const updateAddress = (id, payload) => api.put(`/customer/addresses/${id}`, payload);
export const deleteAddress = (id) => api.delete(`/customer/addresses/${id}`);
export const setDefaultAddress = (id) => api.put(`/customer/addresses/${id}/default`);

// ---------------- Favorites ----------------
export const getFavoriteFoods = () => api.get("/customer/favorites/foods");
export const addFavoriteFood = (foodId) => api.post(`/customer/favorites/foods/${foodId}`);
export const removeFavoriteFood = (foodId) => api.delete(`/customer/favorites/foods/${foodId}`);
export const getFavoriteRestaurants = () => api.get("/customer/favorites/restaurants");
export const addFavoriteRestaurant = (id) => api.post(`/customer/favorites/restaurants/${id}`);
export const removeFavoriteRestaurant = (id) => api.delete(`/customer/favorites/restaurants/${id}`);
export const getFavoriteStatus = (foodIds = [], restaurantIds = []) =>
  api.get("/customer/favorites/status", { params: { food_ids: foodIds.join(","), restaurant_ids: restaurantIds.join(",") } });

// ---------------- Reviews ----------------
export const getFoodReviews = (foodId) => api.get(`/foods/${foodId}/reviews`);
export const createReview = (payload) => api.post("/customer/reviews", payload);
export const getMyReviews = () => api.get("/customer/reviews/mine");
export const getReviewableItems = () => api.get("/customer/reviews/reviewable");
export const updateReview = (id, payload) => api.put(`/customer/reviews/${id}`, payload);
export const deleteReview = (id) => api.delete(`/customer/reviews/${id}`);
export const restaurantListReviews = () => api.get("/restaurant/reviews");
export const restaurantReplyToReview = (id, reply_text) => api.post(`/restaurant/reviews/${id}/reply`, { reply_text });

// ---------------- Cart: combos ----------------
export const addComboToCart = (comboId, quantity = 1) => api.post("/cart/add-combo", { combo_id: comboId, quantity });

// ---------------- Combos (public browse + restaurant manage) ----------------
export const getPublicCombos = (restaurantId) =>
  api.get("/combos", { params: restaurantId ? { restaurant_id: restaurantId } : {} });
export const getOwnCombos = () => api.get("/restaurant/combos");
export const createCombo = (payload) => api.post("/restaurant/combos", payload);
export const updateCombo = (id, payload) => api.put(`/restaurant/combos/${id}`, payload);
export const deleteCombo = (id) => api.delete(`/restaurant/combos/${id}`);

// ---------------- Flash Sales ----------------
export const getOwnFlashSales = () => api.get("/restaurant/flash-sales");
export const createFlashSale = (payload) => api.post("/restaurant/flash-sales", payload);
export const updateFlashSale = (id, payload) => api.put(`/restaurant/flash-sales/${id}`, payload);
export const deleteFlashSale = (id) => api.delete(`/restaurant/flash-sales/${id}`);

// ---------------- Inventory ----------------
export const updateFoodInventory = (foodId, payload) => api.put(`/restaurant/foods/${foodId}/inventory`, payload);

// ---------------- One-Tap Reorder ----------------
export const reorderOrder = (orderId) => api.post(`/customer/reorder/${orderId}`);

// ---------------- Scheduled Orders ----------------
export const getScheduledOrders = () => api.get("/customer/scheduled-orders");
export const createScheduledOrder = (payload) => api.post("/customer/scheduled-orders", payload);
export const cancelScheduledOrder = (id) => api.delete(`/customer/scheduled-orders/${id}`);

// ---------------- AI Meal Planner ----------------
export const createMealPlan = (payload) => api.post("/customer/meal-planner", payload);
export const getMealPlans = () => api.get("/customer/meal-planner");
export const getMealPlan = (id) => api.get(`/customer/meal-planner/${id}`);
export const buildCartFromMealPlan = (id) => api.post(`/customer/meal-planner/${id}/build-cart`);

// ---------------- Group Ordering ----------------
export const createGroupOrder = (payload) => api.post("/customer/group-orders", payload);
export const listMyGroupOrders = () => api.get("/customer/group-orders/mine");
export const joinGroupOrder = (invite_code) => api.post("/customer/group-orders/join", { invite_code });
export const getGroupOrder = (id) => api.get(`/customer/group-orders/${id}`);
export const addGroupOrderItem = (id, food_id, quantity = 1) => api.post(`/customer/group-orders/${id}/items`, { food_id, quantity });
export const removeGroupOrderItem = (id, itemId) => api.delete(`/customer/group-orders/${id}/items/${itemId}`);
export const lockGroupOrder = (id) => api.put(`/customer/group-orders/${id}/lock`);
export const checkoutGroupOrder = (id, payload) => api.post(`/customer/group-orders/${id}/checkout`, payload);
export const cancelGroupOrder = (id) => api.put(`/customer/group-orders/${id}/cancel`);
export const getGroupOrderSuggestions = (id) => api.get(`/customer/group-orders/${id}/suggestions`);
export const suggestGroupOrderDish = (id, food_id) => api.post(`/customer/group-orders/${id}/suggestions`, { food_id });
export const voteForSuggestion = (id, suggestionId) => api.post(`/customer/group-orders/${id}/suggestions/${suggestionId}/vote`);
export const unvoteSuggestion = (id, suggestionId) => api.delete(`/customer/group-orders/${id}/suggestions/${suggestionId}/vote`);
export const finalizeGroupVoting = (id) => api.post(`/customer/group-orders/${id}/finalize-voting`);
export const splitGroupBill = (id, split_type) => api.post(`/customer/group-orders/${id}/split-bill`, { split_type });
export const getGroupBillSplit = (id) => api.get(`/customer/group-orders/${id}/bill-split`);
export const payGroupShare = (id) => api.post(`/customer/group-orders/${id}/pay-share`);
export const refundGroupMemberShare = (id, targetCustomerId) => api.post(`/customer/group-orders/${id}/refund-share/${targetCustomerId}`);

// ---------------- Batch 2: Surplus Deals ----------------
export const getLiveSurplusDeals = () => api.get("/surplus-deals");
export const getOwnSurplusDeals = () => api.get("/restaurant/surplus-deals");
export const createSurplusDeal = (payload) => api.post("/restaurant/surplus-deals", payload);
export const updateSurplusDeal = (id, payload) => api.put(`/restaurant/surplus-deals/${id}`, payload);
export const deleteSurplusDeal = (id) => api.delete(`/restaurant/surplus-deals/${id}`);
export const adminListSurplusDeals = () => api.get("/admin/surplus-deals");

// ---------------- Batch 2: Packing Photo Proof ----------------
export const uploadPackingProof = (orderId, file) => {
  const formData = new FormData();
  formData.append("image", file);
  return api.post(`/orders/${orderId}/packing-proof`, formData, { headers: { "Content-Type": "multipart/form-data" } });
};
// Packing proof is access-controlled (customer/restaurant/admin only) --
// it CANNOT be a plain <img src> since that sends no auth header. Fetch as
// a blob through the authenticated axios instance instead, then render
// with URL.createObjectURL (see PackingProofViewer usage in OrdersPage).
export const fetchPackingProofBlob = (orderId) => api.get(`/orders/${orderId}/packing-proof`, { responseType: "blob" });

// ---------------- Batch 2: Dynamic Tipping ----------------
export const getTipSuggestions = (subtotal) => api.get("/orders/tip-suggestions", { params: { subtotal } });

// ---------------- Batch 2: Recipe-to-Order ----------------
export const matchRecipeFromUrl = (url) => api.post("/customer/recipe-match/url", { url });
export const matchRecipeFromIngredients = (ingredients) => api.post("/customer/recipe-match/manual", { ingredients });

// ---------------- Photo Reorder ----------------
export const matchDishFromPhoto = (file, nearbyOnly = true) => {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("nearby_only", nearbyOnly ? "true" : "false");
  return api.post("/customer/photo-reorder/photo", formData, { headers: { "Content-Type": "multipart/form-data" } });
};
export const matchDishFromName = (dishName, nearbyOnly = true) =>
  api.post("/customer/photo-reorder/manual", { dish_name: dishName, nearby_only: nearbyOnly });

// ---------------- Batch 2: Nutrition Tracking ----------------
export const previewOrderNutrition = (orderId) => api.get(`/customer/nutrition/preview/${orderId}`);
export const logOrderNutrition = (orderId) => api.post("/customer/nutrition/log", { order_id: orderId });
export const getNutritionSummary = (range = "daily") => api.get("/customer/nutrition/summary", { params: { range } });
export const exportNutritionData = () => api.get("/customer/nutrition/export");

// ---------------- Referrals ----------------
export const getMyReferrals = () => api.get("/customer/referrals");

// ---------------- Order Tracking ----------------
export const getOrderTracking = (orderId) => api.get(`/orders/${orderId}/tracking`);

// ---------------- QuickBite Pass ----------------
export const getPassPlans = () => api.get("/customer/pass/plans");
export const getMyPass = () => api.get("/customer/pass");
export const subscribeToPass = (plan_id) => api.post("/customer/pass/subscribe", { plan_id });
export const cancelPass = () => api.put("/customer/pass/cancel");

// ---------------- Restaurant Subscriptions ----------------
export const getAvailableSubscriptionPlans = () => api.get("/restaurant/subscription/plans");
export const getMySubscription = () => api.get("/restaurant/subscription");
export const requestSubscription = (plan_id) => api.post("/restaurant/subscription/request", { plan_id });

// ---------------- Sponsored Restaurants ----------------
export const getSponsoredRestaurants = (placement = "homepage") => api.get("/sponsored", { params: { placement } });

// ---------------- Admin: Fraud Center ----------------
export const getFraudFlags = (status) => api.get("/admin/fraud", { params: status ? { status } : {} });
export const runFraudScan = () => api.post("/admin/fraud/scan");
export const setFraudFlagStatus = (id, status) => api.put(`/admin/fraud/${id}/status`, { status });

// ---------------- Admin: Peak-Hour Analytics & Heatmap ----------------
export const getPeakHourAnalytics = (range = "7d") => api.get("/admin/analytics/peak-hours", { params: { range } });
export const getOrderHeatmap = (range = "7d") => api.get("/admin/analytics/heatmap", { params: { range } });

// ---------------- Admin: Promotion A/B Testing ----------------
export const getPromotionExperiments = () => api.get("/admin/promotions");
export const createPromotionExperiment = (payload) => api.post("/admin/promotions", payload);
export const setPromotionExperimentStatus = (id, status) => api.put(`/admin/promotions/${id}/status`, { status });

// ---------------- Disputes ----------------
export const createDispute = (payload) => api.post("/customer/disputes", payload);
export const getMyDisputes = () => api.get("/customer/disputes");
export const getMyDispute = (id) => api.get(`/customer/disputes/${id}`);
export const getAdminDisputes = (status) => api.get("/admin/disputes", { params: status ? { status } : {} });
export const getAdminDispute = (id) => api.get(`/admin/disputes/${id}`);
export const setAdminDisputeStatus = (id, status, note) => api.put(`/admin/disputes/${id}/status`, { status, note });
export const resolveAdminDispute = (id, payload) => api.post(`/admin/disputes/${id}/resolve`, payload);

// ---------------- Admin: Restaurant Subscriptions & Pass Plans (management) ----------------
export const getAdminSubscriptionPlans = () => api.get("/admin/subscriptions/plans");
export const createAdminSubscriptionPlan = (payload) => api.post("/admin/subscriptions/plans", payload);
export const getAdminSubscriptions = (status) => api.get("/admin/subscriptions", { params: status ? { status } : {} });
export const activateAdminSubscription = (id) => api.put(`/admin/subscriptions/${id}/activate`);
export const cancelAdminSubscription = (id) => api.put(`/admin/subscriptions/${id}/cancel`);
export const getAdminPassPlans = () => api.get("/admin/pass-plans");
export const createAdminPassPlan = (payload) => api.post("/admin/pass-plans", payload);

// ---------------- Admin: Sponsored Campaigns (management) ----------------
export const getAdminSponsoredCampaigns = () => api.get("/admin/sponsored");
export const createAdminSponsoredCampaign = (payload) => api.post("/admin/sponsored", payload);
export const deleteAdminSponsoredCampaign = (id) => api.delete(`/admin/sponsored/${id}`);

// ---------------- Admin: Referral config ----------------
export const getAdminReferralConfig = () => api.get("/admin/referrals/config");
export const updateAdminReferralConfig = (payload) => api.put("/admin/referrals/config", payload);
export const getAdminReferrals = () => api.get("/admin/referrals");


// ---------------- Admin ----------------
export const getAdminDashboard = () => api.get("/admin/dashboard");
export const getAdminAnalytics = () => api.get("/admin/analytics");
export const adminListRestaurants = (params) => api.get("/admin/restaurants", { params });
export const adminGetRestaurant = (id) => api.get(`/admin/restaurants/${id}`);
export const adminApproveRestaurant = (id) => api.put(`/admin/restaurants/${id}/approve`);
export const adminRejectRestaurant = (id) => api.put(`/admin/restaurants/${id}/reject`);
export const adminSetRestaurantStatus = (id, status) => api.put(`/admin/restaurants/${id}/status`, { status });
export const adminDeleteRestaurant = (id) => api.delete(`/admin/restaurants/${id}`);
export const adminRestaurantOrders = (id) => api.get(`/admin/restaurants/${id}/orders`);

export const adminListCustomers = (params) => api.get("/admin/customers", { params });
export const adminGetCustomer = (id) => api.get(`/admin/customers/${id}`);
export const adminSetCustomerStatus = (id, is_active) => api.put(`/admin/customers/${id}/status`, { is_active });

export const adminListCategories = () => api.get("/admin/categories");
export const adminAddCategory = (payload) => api.post("/admin/categories", payload);
export const adminUpdateCategory = (id, payload) => api.put(`/admin/categories/${id}`, payload);
export const adminDeleteCategory = (id) => api.delete(`/admin/categories/${id}`);

export const adminListFoods = () => api.get("/admin/foods");
export const adminUpdateFood = (id, payload) => api.put(`/admin/foods/${id}`, payload);
export const adminDeleteFood = (id) => api.delete(`/admin/foods/${id}`);

export const adminListOrders = (params) => api.get("/admin/orders", { params });
export const adminListPayments = (params) => api.get("/admin/payments", { params });

export const adminListQuestions = () => api.get("/admin/game-questions");
export const adminAddQuestion = (payload) => api.post("/admin/game-questions", payload);
export const adminUpdateQuestion = (id, payload) => api.put(`/admin/game-questions/${id}`, payload);
export const adminDeleteQuestion = (id) => api.delete(`/admin/game-questions/${id}`);
export const adminGameStats = () => api.get("/admin/game-stats");

// ---------------- Admin: Loyalty Management ----------------
export const adminListCustomerLoyalty = (params) => api.get("/admin/loyalty/customers", { params });
export const adminGetCustomerLoyalty = (id) => api.get(`/admin/loyalty/customer/${id}`);
export const adminAdjustCustomerPoints = (id, delta, reason) =>
  api.post(`/admin/loyalty/customer/${id}/adjust`, { delta, reason });
export const adminListLoyaltyLevels = () => api.get("/admin/loyalty/levels");
export const adminUpdateLoyaltyLevel = (id, payload) => api.put(`/admin/loyalty/levels/${id}`, payload);

// ---------------- Admin: Authority Management ----------------
export const adminListPermissions = (userType) => api.get("/admin/authorities/permissions", { params: userType ? { user_type: userType } : {} });
export const adminListCustomerAuthorities = (params) => api.get("/admin/authorities/customers", { params });
export const adminGetCustomerAuthority = (id) => api.get(`/admin/authorities/customer/${id}`);
export const adminUpdateCustomerAuthority = (id, permission_key, is_allowed, reason) =>
  api.put(`/admin/authorities/customer/${id}`, { permission_key, is_allowed, reason });
export const adminListRestaurantAuthorities = (params) => api.get("/admin/authorities/restaurants", { params });
export const adminGetRestaurantAuthority = (id) => api.get(`/admin/authorities/restaurant/${id}`);
export const adminUpdateRestaurantAuthority = (id, permission_key, is_allowed, reason) =>
  api.put(`/admin/authorities/restaurant/${id}`, { permission_key, is_allowed, reason });
export const adminAuthorityAuditLogs = (params) => api.get("/admin/authorities/audit-logs", { params });

// ---------------- Batch 1: Moods & Allergens ----------------
export const getMoods = () => api.get("/moods");
export const getAllergens = () => api.get("/allergens");

// ---------------- Batch 1: Live Kitchen Load ----------------
export const getOwnKitchenStatus = () => api.get("/restaurant/kitchen-status");
export const updateKitchenStatus = (payload) => api.put("/restaurant/kitchen-status", payload);

// ---------------- Batch 1: Chef's Specials ----------------
export const getLiveChefSpecials = () => api.get("/chef-specials");
export const getOwnChefSpecials = () => api.get("/restaurant/chef-specials");
export const createChefSpecial = (payload) => api.post("/restaurant/chef-specials", payload);
export const updateChefSpecial = (id, payload) => api.put(`/restaurant/chef-specials/${id}`, payload);
export const deleteChefSpecial = (id) => api.delete(`/restaurant/chef-specials/${id}`);
export const adminListChefSpecials = () => api.get("/admin/chef-specials");
export const adminDeleteChefSpecial = (id) => api.delete(`/admin/chef-specials/${id}`);

// ---------------- Batch 1: Food Streaks ----------------
export const getFoodStreak = () => api.get("/customer/streak");

