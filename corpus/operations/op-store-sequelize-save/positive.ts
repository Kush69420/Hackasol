export async function changeAddress (address: any, req: any) {
  address.streetAddress = req.body.streetAddress
  await address.save()
}
