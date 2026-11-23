import { ThingModel } from '../models/thing'
export function excluded() {
  return async (req, res) => {
    const things = await ThingModel.findAll({ attributes: { exclude: ['email'] } })
    res.json(things)
  }
}
export function included() {
  return async (req, res) => {
    const things = await ThingModel.findAll({ attributes: ['email'] })
    res.json(things)
  }
}
export function mapped() {
  return async (req, res) => {
    const things = await ThingModel.findAll()
    res.json(things.map(x => ({ email: x.email })))
  }
}
export function omitted() {
  return async (req, res) => {
    const things = await ThingModel.findAll()
    res.json(things.map(x => ({ other: x.other })))
  }
}
export function masked() {
  return async (req, res) => {
    const thing = await ThingModel.findOne()
    const unrelated = 'hello'.slice(1)
    res.json({ email: thing.email.replace(/./g, '*'), other: unrelated })
  }
}
export function unmasked() {
  return async (req, res) => {
    const thing = await ThingModel.findOne()
    const unrelated = 'hello'.slice(1)
    res.json({ email: thing.email, other: unrelated })
  }
}
export function objectOmitted() {
  return async (req, res) => {
    const thing = await ThingModel.findOne()
    res.send({ other: thing.other })
  }
}
export function maskFunction() {
  return async (req, res) => {
    const thing = await ThingModel.findOne()
    res.send({ email: mask(thing.email) })
  }
}
