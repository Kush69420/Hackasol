import morgan from 'morgan'
import helmet from 'helmet'
import express from 'express'

export function hardening (app: express.Express) {
  app.use(helmet())
}
