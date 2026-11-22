export async function checkAddress (address: any) {
  await address.reload()
  return address.validate()
}
