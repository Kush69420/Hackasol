export function account() { return (req, res) => { const principal = security.authenticatedUsers.get(req); res.json({ email: principal.email }) } }
