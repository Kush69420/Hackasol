import { reviewsCollection } from '../data/db'
export function writeReview() { return (req, res) => { reviewsCollection.insert({ author: req.body.author, message: req.body.message }); res.json({ok: true}) } }
export function readReviews() { return (req, res) => { reviewsCollection.find({}).then((records) => { res.json(records.map(record => ({ message: record.message }))) }) } }
