import { ThingModel } from './models/thing'
const resources = [{ name: 'Things', model: ThingModel }]
for (const { name, model } of resources) {
  finale.resource({ model, endpoints: [`/api/${name}`, `/api/${name}/:id`] })
}
