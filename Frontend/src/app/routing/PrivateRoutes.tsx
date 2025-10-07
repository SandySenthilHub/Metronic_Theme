import { FC, Suspense, useEffect } from 'react'
import { Route, Routes, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { MasterLayout } from '../../_metronic/layout/MasterLayout'
import TopBarProgress from 'react-topbar-progress-indicator'
import { getCSSVariableValue } from '../../_metronic/assets/ts/_utils'
import { WithChildren } from '../../_metronic/helpers'

// Pages
import { DashboardWrapper } from '../pages/dashboard/DashboardWrapper'
import ClaimProcessing from '../pages/menus/ClaimProcessing'
import ProcessingResults from '../pages/menus/ProcessingResults'
import PolicyQA from '../pages/menus/PolicyQA'
import WorkshopSuggestion from '../pages/menus/WorkshopSuggestion'

// Wrapper for ClaimProcessing to handle props and navigation
const ClaimProcessingRoute = () => {
  const navigate = useNavigate()

  const handleProcessClaim = (documents: any[]) => {
    // Navigate to ProcessingResults page and pass documents as state
    navigate('/claims-result', { state: { documents } })
  }

  return (
    <ClaimProcessing
      onBack={() => navigate('/dashboard')}
      onProcessClaim={handleProcessClaim}
    />
  )
}

// Wrapper for ProcessingResults to get state
const ProcessingResultsRoute = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const documents = location.state?.documents || []

  // Redirect if no documents
  useEffect(() => {
    if (!documents.length) {
      navigate('/dashboard', { replace: true })
    }
  }, [documents, navigate])

  if (!documents.length) return null

  return <ProcessingResults onBack={() => navigate('/dashboard')} documents={documents} />
}

// Optional Suspense wrapper
const SuspensedView: FC<WithChildren> = ({ children }) => {
  const baseColor = getCSSVariableValue('--bs-primary')
  TopBarProgress.config({
    barColors: { '0': baseColor },
    barThickness: 1,
    shadowBlur: 5,
  })
  return <Suspense fallback={<TopBarProgress />}>{children}</Suspense>
}

const PrivateRoutes = () => {
  return (
    <Routes>
      <Route element={<MasterLayout />}>
        {/* Main Pages */}
        <Route path="dashboard" element={<DashboardWrapper />} />
        <Route path="claims-new" element={<ClaimProcessingRoute />} />
        <Route path="claims-result" element={<ProcessingResultsRoute />} />
        <Route path="policy-qa" element={<PolicyQA />} />
        <Route path="workshop" element={<WorkshopSuggestion />} />

        {/* Fallback for unmatched routes */}
        <Route path="*" element={<Navigate to="/error/404" />} />
      </Route>
    </Routes>
  )
}

export { PrivateRoutes }
