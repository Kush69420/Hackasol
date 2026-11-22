export async function review (db: any, user: any, req: any) {
  await db.reviewsCollection.insert({ message: req.body.message, author: user.email })
}
