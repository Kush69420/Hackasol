import express from 'express'
import { writeReview, readReviews } from './routes/reviews'
import { account } from './routes/account'
const app = express()
app.get('/account', account())
app.get('/reviews', readReviews())
app.put('/reviews', writeReview())
