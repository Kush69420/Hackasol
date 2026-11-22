import logger from '../lib/logger'

export function scoped (user: any) {
  logger.info('Session scoped')
  return logger.child({ email: user.email })
}
