import express from "express"
import { lookup } from "./routes/users"
const app = express()
app.get("/api/users/:email", lookup())
