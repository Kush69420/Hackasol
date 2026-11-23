import { ThingModel } from './models/thing'
const resources = [{ name: 'Things', model: ThingModel }]
for (const { name, model } of resources) {
  const resource = finale.resource({ model, endpoints: [`/api/${name}`, `/api/${name}/:id`] })
  resource.all.send.before((req, res, context) => {
    context.instance = { status: 'success', data: context.instance }
    return context.continue
  })
}
