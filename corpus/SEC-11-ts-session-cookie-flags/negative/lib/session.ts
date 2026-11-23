export const remember = (res, token: string) => { res.cookie('token', token, { httpOnly: true, secure: true, sameSite: 'strict' }) }
