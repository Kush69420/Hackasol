export const reviewsCollection = new MarsDB.Collection('posts')
db.reviewsCollection.insert({ author: name, message: text })
db.reviewsCollection.update({ author: name }, { $set: { rating: stars } })
