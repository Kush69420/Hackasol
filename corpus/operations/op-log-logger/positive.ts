import logger from '../lib/logger'

export function onFailure (user: any) {
  logger.warn('Failed login for ' + user.email)
}
