import morgan from 'morgan'
import express from 'express'

export function accessLog (app: express.Express, stream: NodeJS.WritableStream) {
  app.use(morgan('combined', { stream }))
}
