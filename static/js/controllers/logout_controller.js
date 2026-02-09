import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.2.2/dist/stimulus.js"

export default class extends Controller {
    async handle(event) {
        event.preventDefault()

        const form = event.target

        try {
            await fetch(form.action, {
                method: 'POST',
                body: new FormData(form),
                credentials: 'same-origin'
            })

            document.cookie.split(";").forEach(function(c) {
                document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/")
            })

            const nextUrl = form.querySelector('input[name="next"]')?.value || '/'
            window.location.href = nextUrl
            window.location.reload(true)
        } catch (error) {
            window.location.href = '/'
        }

        return false
    }
}
