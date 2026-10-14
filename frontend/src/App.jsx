import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import HomePage from './pages/HomePage'
import DashboardPage from './pages/DashboardPage'
import RegisterPage from './pages/RegisterPage'
import PlannerPage from './pages/PlannerPage'
import WaterBudgetPage from './pages/WaterBudgetPage'
import ScenarioPage from './pages/ScenarioPage'
import HistoryPage from './pages/HistoryPage'
import KnowledgePage from './pages/KnowledgePage'

export default function App() {
  const [activeFarmerId, setActiveFarmerId] = useState(
    () => parseInt(localStorage.getItem('activeFarmerId') || '0') || null
  )

  const selectFarmer = (id) => {
    setActiveFarmerId(id)
    localStorage.setItem('activeFarmerId', String(id))
  }

  return (
    <BrowserRouter>
      <div className="page-wrap">
        <Navbar activeFarmerId={activeFarmerId} onSelectFarmer={selectFarmer} />
        <main className="main-content">
          <Routes>
            <Route path="/"          element={<HomePage onSelectFarmer={selectFarmer} />} />
            <Route path="/register"  element={<RegisterPage onSelectFarmer={selectFarmer} />} />
            <Route path="/dashboard" element={<DashboardPage farmerId={activeFarmerId} />} />
            <Route path="/planner"   element={<PlannerPage farmerId={activeFarmerId} />} />
            <Route path="/budget"    element={<WaterBudgetPage farmerId={activeFarmerId} />} />
            <Route path="/scenarios" element={<ScenarioPage farmerId={activeFarmerId} />} />
            <Route path="/history"   element={<HistoryPage farmerId={activeFarmerId} />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="*"          element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  )
}
