import { useIntl } from 'react-intl'
import { KTIcon } from '../../../../helpers'
import { SidebarMenuItemWithSub } from './SidebarMenuItemWithSub'
import { SidebarMenuItem } from './SidebarMenuItem'
import {
  FileText,
  CheckCircle,
  Clock,
  DollarSign,
  Shield,

} from 'lucide-react'


const SidebarMenuMain = () => {
  const intl = useIntl()

  return (
    <>
      <SidebarMenuItem
        to='/dashboard'
        icon='element-11'
        title={intl.formatMessage({ id: 'MENU.DASHBOARD' })}
        fontIcon='bi-app-indicator'
      />
      <SidebarMenuItem
        to='/policy-qa'
        icon='book'
        title='Policy Q&A'
        fontIcon='bi-book'
      />

      <SidebarMenuItem
        to='/claims-new'
        icon='element-3'       
        title='Claim Processing'
        fontIcon='bi-file-text' 
      />


      <SidebarMenuItem
        to='/workshop'
        icon='shield'
        title='Workshop Suggestion'
        fontIcon='bi-shield'
      />


    </>
  )
}

export { SidebarMenuMain }
