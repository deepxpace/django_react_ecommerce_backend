import { useState, useEffect, createContext } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";
import { Helmet } from "react-helmet";
import { CartContext, CartProvider } from "./views/plugin/Context";

import MainWrapper from "./layout/MainWrapper";
import Register from "./views/auth/Register";
import Login from "./views/auth/Login";
import ForgotPassword from "./views/auth/ForgotPassword";
import CreatePassword from "./views/auth/CreatePassword";
import Logout from "./views/auth/Logout";

import Products from "./views/store/Products";
import ProductDetail from "./views/store/ProductDetail";
import Search from "./views/store/Search";
import Cart from "./views/store/Cart";
import Checkout from "./views/store/Checkout";
import PaymentSuccess from "./views/store/PaymentSuccess";
import Orders from "./views/customer/Orders";
import OrderDetail from "./views/customer/OrderDetail";
import Account from "./views/customer/Account";
import Wishlist from "./views/customer/Wishlist";
import CustomerNotification from "./views/customer/CustomerNotification";
import Invoice from "./views/customer/Invoice";
import CustomerSettings from "./views/customer/CustomerSettings";

import Dashboard from "./views/vendor/Dashboard";
import Earning from "./views/vendor/Earning";
import OrdersVendor from "./views/vendor/OrdersVendor";
import OrderDetailVendor from "./views/vendor/OrderDetailVendor";
import NotificationVendor from "./views/vendor/NotificationVendor";
import ReviewsVendor from "./views/vendor/Reviews";
import Coupon from "./views/vendor/Coupon";
import Shop from "./views/vendor/Shop";
import SettingsVendor from "./views/vendor/SettingsVendor";
import ProductsVendor from "./views/vendor/ProductsVendor";
import AddProduct from "./views/vendor/AddProduct";
import UpdateProduct from "./views/vendor/UpdateProduct";

import ProtectedRoute from "./components/ProtectedRoute";
import ApiDebug from "./components/ApiDebug"; // Import the ApiDebug component

// Error boundary component
const NoMatch = () => {
  let location = useLocation();
  return (
    <div className="container mt-5">
      <div className="row">
        <div className="col-md-12 text-center">
          <div className="error-template">
            <h1>Oops!</h1>
            <h2>404 Not Found</h2>
            <div className="error-details">
              No match for <code>{location.pathname}</code>
            </div>
            <div className="error-actions mt-4">
              <a href="/" className="btn btn-primary btn-lg">
                <i className="fas fa-home me-2"></i>
                Take Me Home
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  const [cartCount, setCartCount] = useState(0);

  return (
    <CartProvider>
      <div className="App">
        <Helmet>
          <meta charSet="utf-8" />
          <title>Koshimart</title>
          <meta name="description" content="Koshimart e-commerce" />
        </Helmet>

        <CartContext.Provider value={[cartCount, setCartCount]}>
          <Router>
            <Routes>
              {/* Debug Route */}
              <Route path="/debug" element={<ApiDebug />} />

              {/* Auth Routes */}
              <Route path="/register" element={<Register />} />
              <Route path="/login" element={<Login />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password/:uid/:token" element={<CreatePassword />} />
              <Route path="/logout" element={<Logout />} />

              {/* Store Routes */}
              <Route path="/" element={<MainWrapper />}>
                <Route index element={<Products />} />
                <Route path="detail/:slug" element={<ProductDetail />} />
                <Route path="search" element={<Search />} />
                <Route path="cart" element={<Cart />} />
                <Route path="checkout" element={<Checkout />} />
                <Route path="payment-success/:oid" element={<PaymentSuccess />} />

                {/* Customer Protected Routes */}
                <Route
                  path="orders"
                  element={
                    <ProtectedRoute>
                      <Orders />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="orders/:oid"
                  element={
                    <ProtectedRoute>
                      <OrderDetail />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="account"
                  element={
                    <ProtectedRoute>
                      <Account />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="wishlist"
                  element={
                    <ProtectedRoute>
                      <Wishlist />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="notifications"
                  element={
                    <ProtectedRoute>
                      <CustomerNotification />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="invoice/:oid"
                  element={
                    <ProtectedRoute>
                      <Invoice />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="settings"
                  element={
                    <ProtectedRoute>
                      <CustomerSettings />
                    </ProtectedRoute>
                  }
                />

                {/* Vendor Protected Routes */}
                <Route
                  path="admin"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/earning"
                  element={
                    <ProtectedRoute>
                      <Earning />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/orders"
                  element={
                    <ProtectedRoute>
                      <OrdersVendor />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/orders/:oid"
                  element={
                    <ProtectedRoute>
                      <OrderDetailVendor />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/notifications"
                  element={
                    <ProtectedRoute>
                      <NotificationVendor />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/reviews"
                  element={
                    <ProtectedRoute>
                      <ReviewsVendor />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/coupons"
                  element={
                    <ProtectedRoute>
                      <Coupon />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/shop"
                  element={
                    <ProtectedRoute>
                      <Shop />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/settings"
                  element={
                    <ProtectedRoute>
                      <SettingsVendor />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/products"
                  element={
                    <ProtectedRoute>
                      <ProductsVendor />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/add-product"
                  element={
                    <ProtectedRoute>
                      <AddProduct />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="admin/update-product/:pid"
                  element={
                    <ProtectedRoute>
                      <UpdateProduct />
                    </ProtectedRoute>
                  }
                />

                {/* 404 Route */}
                <Route path="*" element={<NoMatch />} />
              </Route>
            </Routes>
          </Router>
        </CartContext.Provider>
      </div>
    </CartProvider>
  );
}

export default App; 