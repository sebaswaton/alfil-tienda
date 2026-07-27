import { Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './layouts/AdminLayout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import ProductsPage from './pages/ProductsPage'
import ProductFormPage from './pages/ProductFormPage'
import BrandsPage from './pages/BrandsPage'
import CategoriesPage from './pages/CategoriesPage'

export default function App() {
  return <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<AdminLayout />}>
        <Route index element={<Navigate to="/productos" replace />} />
        <Route path="/productos" element={<ProductsPage />} />
        <Route path="/productos/nuevo" element={<ProductFormPage />} />
        <Route path="/productos/:id/editar" element={<ProductFormPage />} />
        <Route path="/marcas" element={<BrandsPage />} />
        <Route path="/categorias" element={<CategoriesPage />} />
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/productos" replace />} />
  </Routes>
}
