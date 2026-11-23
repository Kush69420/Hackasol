const defaults = { httpOnly: true, secure: true, sameSite: 'strict' }
export const secureSession = (res, token) => res.cookie('token', token, { ...defaults })
export const unknownSession = (res, token, options) => res.cookie('token', token, { ...options })
