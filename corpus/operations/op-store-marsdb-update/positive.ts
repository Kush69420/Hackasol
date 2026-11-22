export async function likeReview (db: any, id: string, user: any) {
  await db.reviewsCollection.update({ _id: id }, { $set: { author: user.email } })
}
