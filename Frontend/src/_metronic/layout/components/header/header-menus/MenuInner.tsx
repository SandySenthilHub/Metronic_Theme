import { useIntl } from 'react-intl'
import { MenuItem } from './MenuItem'
import { MenuInnerWithSub } from './MenuInnerWithSub'
import { MegaMenu } from './MegaMenu'

export function MenuInner() {
  const intl = useIntl()
  return (
    <>
      <MenuItem title={intl.formatMessage({ id: 'MENU.DASHBOARD' })} to='/dashboard' />
      <MenuItem title='Policy Q&A' to='/policy-qa' />
      <MenuItem title='Claim Processing' to='/claims-new' />
      <MenuItem title='Workshop Suggestion' to='/workshop' />

    </>
  )
}
