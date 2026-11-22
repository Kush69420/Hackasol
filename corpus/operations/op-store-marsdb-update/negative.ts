export async function reviewsBy (db: any, user: any) {
  return db.reviewsCollection.find({ author: user.email })
}
