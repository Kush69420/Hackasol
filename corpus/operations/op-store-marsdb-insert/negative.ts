export async function reviewsBy (db: any, user: any, doc: object) {
  await db.reviewsCollection.insert(doc)
  return db.reviewsCollection.find({ author: user.email })
}
