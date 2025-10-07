import { FC, useState } from 'react'
import { useIntl } from 'react-intl'
import { PageTitle } from '../../../_metronic/layout/core'
import { ToolbarWrapper } from '../../../_metronic/layout/components/toolbar'
import { Content } from '../../../_metronic/layout/components/content'
import { useNavigate } from 'react-router-dom'
import {
  FileText,
  CheckCircle,
  Clock,
  DollarSign,
  Shield,
  Car,
  Building2,
  Filter,
  MoreVertical,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'

interface DashboardProps { }

const InsuranceDashboardPage: FC<DashboardProps> = () => {
  const navigate = useNavigate()
  const intl = useIntl()
  const [selectedPeriod, setSelectedPeriod] = useState('7d')

  const stats = [
    {
      title: 'Total Claims',
      value: '2,847',
      change: '+12.5%',
      trend: 'up',
      icon: FileText,
      color: 'primary',
    },
    {
      title: 'Approved Claims',
      value: '2,234',
      change: '+8.2%',
      trend: 'up',
      icon: CheckCircle,
      color: 'success',
    },
    {
      title: 'Processing Time',
      value: '2.4 days',
      change: '-15.3%',
      trend: 'down',
      icon: Clock,
      color: 'info',
    },
    {
      title: 'Total Payout',
      value: 'AED 1.2M',
      change: '+22.1%',
      trend: 'up',
      icon: DollarSign,
      color: 'warning',
    },
  ]

  const recentClaims = [
    { id: 'CLM-2025-001', customer: 'Ahmed Al Mansouri', type: 'Vehicle Damage', amount: 'AED 15,420', status: 'approved', date: '2 hours ago', avatar: 'AM' },
    { id: 'CLM-2025-002', customer: 'Sarah Johnson', type: 'Theft Coverage', amount: 'AED 45,200', status: 'processing', date: '4 hours ago', avatar: 'SJ' },
    { id: 'CLM-2025-003', customer: 'Mohammed Hassan', type: 'Accident Claim', amount: 'AED 8,750', status: 'pending', date: '6 hours ago', avatar: 'MH' },
    { id: 'CLM-2025-004', customer: 'Lisa Chen', type: 'Glass Damage', amount: 'AED 2,100', status: 'approved', date: '1 day ago', avatar: 'LC' },
  ]

  const quickActions = [
    // { title: 'Navigation Menu', description: 'Access original app features', icon: Shield, color: 'primary', action: () => navigate('/') },
    { title: 'Policy Q&A', description: 'Ask questions about central government details or insurance policies.', icon: Shield, color: 'success', action: () => navigate('/policy-qa') },
    { title: 'New Claim', description: 'Upload required documents for claim analysis.', icon: FileText, color: 'info', action: () => navigate('/claims-new') },
    { title: 'Workshop Analysis', description: 'Upload 3 workshop summaries for car damage analysis and suggestion.', icon: Building2, color: 'danger', action: () => navigate('/workshop') },
    // { title: 'Vehicle Inspection', description: 'Schedule inspection', icon: Car, color: 'warning', action: () => {} },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'badge-light-success'
      case 'processing':
        return 'badge-light-info'
      case 'pending':
        return 'badge-light-warning'
      case 'rejected':
        return 'badge-light-danger'
      default:
        return 'badge-light'
    }
  }

  return (
    <>
      <ToolbarWrapper />
      <Content>
        {/* Stats Row */}
        <div className='row g-5 g-xl-10 mb-5 mb-xl-10'>
          {stats.map((stat, idx) => {
            const Icon = stat.icon
            return (
              <div key={idx} className='col-md-6 col-lg-6 col-xl-3'>
                <div className={`card card-xl-stretch mb-xl-8 bg-light-${stat.color}`}>
                  <div className='card-body'>
                    <div className='d-flex align-items-center justify-content-between mb-4'>
                      <div className={`symbol symbol-40px bg-${stat.color}`}>
                        <Icon className='text-white' size={18} />
                      </div>
                      <div className={`fw-bold fs-7 ${stat.trend === 'up' ? 'text-success' : 'text-danger'}`}>
                        {stat.trend === 'up' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}{' '}
                        {stat.change}
                      </div>
                    </div>
                    <div>
                      <div className='fs-2hx fw-bold text-gray-800'>{stat.value}</div>
                      <div className='fs-6 fw-semibold text-gray-600'>{stat.title}</div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Recent Claims & Quick Actions */}
        <div className='row g-5 g-xl-10'>
          {/* Recent Claims */}
          {/* <div className='col-xl-8'>
            <div className='card card-xl-stretch mb-xl-8'>
              <div className='card-header border-0 pt-5 d-flex justify-content-between'>
                <h3 className='card-title align-items-start flex-column'>
                  <span className='card-label fw-bold fs-3 text-gray-800'>Recent Claims</span>
                </h3>
                <div>
                  <button className='btn btn-sm btn-light me-2'>
                    <Filter size={16} />
                  </button>
                  <button className='btn btn-sm btn-light'>
                    <MoreVertical size={16} />
                  </button>
                </div>
              </div>
              <div className='card-body pt-3'>
                {recentClaims.map((claim) => (
                  <div key={claim.id} className='d-flex align-items-center justify-content-between py-3 border-bottom'>
                    <div className='d-flex align-items-center'>
                      <div className='symbol symbol-40px me-3 bg-primary text-white fw-bold'>{claim.avatar}</div>
                      <div>
                        <div className='fw-bold fs-6 text-gray-800'>{claim.customer}</div>
                        <div className='text-muted fs-7'>{claim.type} • {claim.id}</div>
                      </div>
                    </div>
                    <div className='text-end'>
                      <div className='fw-bold fs-6 text-gray-800'>{claim.amount}</div>
                      <div className='d-flex align-items-center justify-content-end gap-2 mt-1'>
                        <span className={`badge ${getStatusColor(claim.status)}`}>{claim.status}</span>
                        <span className='text-gray-500 fs-8'>{claim.date}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className='card-footer py-3 text-center'>
                <button className='btn btn-sm btn-primary'>View All Claims</button>
              </div>
            </div>
          </div> */}

          {/* Quick Actions */}
          <div className="">
            <div className="card card-xl-stretch mb-xl-8">
              <div className="card-header border-0 pt-5">
                <h3 className="card-title fw-bold fs-3 text-gray-800">Quick Actions</h3>
              </div>
              <div className="card-body d-flex flex-row gap-4">
                {quickActions.map((action, idx) => {
                  const Icon = action.icon
                  const bgColors = ['#E3F2FD', '#FFF3E0', '#E8F5E9', '#F3E5F5', '#FFFDE7']
                  const defaultBg = bgColors[idx % bgColors.length]

                  return (
                    <div
                      key={idx}
                      onClick={action.action}
                      className="d-flex align-items-center w-100 p-4 rounded-3 cursor-pointer transition"
                      style={{
                        background: defaultBg,
                        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                        transition: 'all 0.3s',
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.background = `linear-gradient(90deg, ${action.color}99 0%, ${action.color}CC 100%)`
                        e.currentTarget.style.boxShadow = '0 6px 15px rgba(0,0,0,0.15)'
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.background = defaultBg
                        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'
                      }}
                    >
                      {/* Icon */}
                      <div
                        className="d-flex align-items-center justify-content-center rounded-3 me-4"
                        style={{
                          width: '60px',
                          height: '60px',
                          background: action.color,
                        }}
                      >
                        <Icon style={{ color: '#000' }} size={24} />
                      </div>

                      {/* Text */}
                      <div className="d-flex flex-column justify-content-center">
                        <div className="fw-bold fs-6 text-gray-900">{action.title}</div>
                        <div className="text-gray-600 fs-8">{action.description}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>



        </div>
      </Content>
    </>
  )
}

const DashboardWrapper: FC = () => {
  const intl = useIntl()
  return (
    <>
      <PageTitle breadcrumbs={[]}>{intl.formatMessage({ id: 'INSURANCE_DASHBOARD' })}</PageTitle>
      <InsuranceDashboardPage />
    </>
  )
}

export { DashboardWrapper }
