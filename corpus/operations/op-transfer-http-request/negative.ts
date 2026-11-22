import http from 'http'
import express from 'express'

export function serve (app: express.Express) {
  return http.createServer(app)
}
