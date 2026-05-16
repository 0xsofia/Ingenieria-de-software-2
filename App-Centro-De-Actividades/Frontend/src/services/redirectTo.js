import { startTransition } from 'react'

export function redirectTo(navigate, path, state) {
  startTransition(() => {
    navigate(path, { replace: true, state })
  })
}
